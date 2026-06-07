"""AnswerEvaluatorAgent — multi-dimensional answer assessment with Agentic RAG.

Extends BaseAgent with source-type-aware tool selection:
  - resume_experience / resume_project → LLM-as-a-Judge ONLY (no RAG tools)
  - knowledge_base → Agentic RAG hybrid evaluation

Key difference from current pipeline: the agent receives ONLY the tools
relevant to its question source type. Resume questions don't get RAG tools
at all — preventing the agent from erroneously searching the knowledge base.
"""

import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent
from app.agents.structured_output import parse_json_response

logger = logging.getLogger(__name__)

# Separated system prompts by evaluation mode — no "choose your own adventure"
LLM_JUDGE_SYSTEM_PROMPT = """你是一个专业的技术面试答案评估Agent。你必须严格按照以下规则工作。

## 核心规则（违反将导致系统错误）
- **禁止使用Markdown格式**：不要使用 ```、表格、**粗体**、- 列表等任何Markdown语法
- **只输出纯JSON**：最终回复必须且只能是{}包裹的JSON对象，前后不能有任何其他文字
- **不要输出思考过程**：不要在JSON之外写任何解释、分析步骤、评估过程

## 评估模式：LLM-as-a-Judge
你只能使用 check_resume_consistency 工具来验证回答与简历的一致性。
这是一道基于候选人简历的题目，不要去检索知识库。

## 评估维度（1-5分）
1. accuracy（真实性）: 是否与简历一致？技术细节是否可信？
2. completeness（完整性）: 是否全面？是否使用STAR法则？
3. clarity（表达清晰度）: 结构清晰？语言流畅？
4. technical_depth（技术深度）: 是否有技术理解深度和实现细节？

## 评分
- overall_score: 0-100（不是维度平均）
- authenticity_flag: "consistent" | "inconsistent" | "uncertain"

## 输出格式 — 严格复制这个JSON结构，只替换值
{"eval_mode":"llm_judge","accuracy":{"score":4,"reasoning":"理由"},"completeness":{"score":3,"reasoning":"理由"},"clarity":{"score":5,"reasoning":"理由"},"technical_depth":{"score":4,"reasoning":"理由"},"overall_score":80.0,"assessment":"综合评价","strengths":["优点"],"areas_for_improvement":["改进点"],"authenticity_flag":"consistent"}
"""

RAG_HYBRID_SYSTEM_PROMPT = """你是一个专业的技术面试答案评估Agent。

## 核心规则（违反将导致系统错误）
- **禁止使用Markdown格式**：不要 ```、表格、**粗体**、- 列表
- **只输出纯JSON**：最终回复只能是{}包裹的JSON对象
- **不要输出思考过程**

## 评估模式：RAG混合评估
你有一个工具：retrieve_reference_answer — 从知识库检索标准答案。

**关键决策**：
- 如果题目已提供有效的"AI参考答案"，**跳过检索**，直接用它评分
- 只有在题目没有参考答案，或参考答案为空时，才使用工具检索
- 工具只需调用一次，得到结果后立即评分

## 输出格式 — 严格复制此JSON结构
{"eval_mode":"rag_hybrid","overall_score":85,"vector_similarity":0.92,"covered_points":["得分点"],"missing_points":["遗漏点"],"assessment":"评价","strengths":["优点"],"areas_for_improvement":["改进点"]}
"""


class AnswerEvaluatorAgent(BaseAgent):
    """Autonomous agent for answer evaluation with source-type-aware tools.

    IMPORTANT: The caller must provide only the tools relevant to the
    question's source_type. Mixing RAG tools with resume questions
    causes the agent to erroneously search the knowledge base.

    - resume_experience/resume_project → provide [check_resume_consistency] only
    - knowledge_base → provide [retrieve_reference_answer, search_knowledge_base_for_fact_check] only
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        eval_mode: str = "llm_judge",  # "llm_judge" or "rag_hybrid"
        max_iterations: int = 3,  # Reduced: fewer decisions needed with mode-specific tools
    ):
        super().__init__(
            llm=llm,
            tools=tools,
            max_iterations=max_iterations,
            name=f"AnswerEvaluator({eval_mode})",
        )
        self.eval_mode = eval_mode

    @property
    def system_prompt(self) -> str:
        if self.eval_mode == "rag_hybrid":
            return RAG_HYBRID_SYSTEM_PROMPT
        return LLM_JUDGE_SYSTEM_PROMPT

    def build_user_message(self, state: Dict[str, Any]) -> str:
        questions = state.get("questions", [])
        answers = state.get("answers", [])
        question_index = state.get("question_index", 0)
        resume_ocr = state.get("resume_ocr", {}) or {}

        current_question = {}
        current_answer = {}
        if question_index < len(questions):
            current_question = questions[question_index]
        if question_index < len(answers):
            current_answer = answers[question_index]

        source_type = current_question.get("source_type", "resume_experience")
        ai_ref = current_question.get("ai_reference_answer", "")
        transcript = current_answer.get("transcript_text", "")

        if self.eval_mode == "rag_hybrid":
            # KB mode: focus on reference answer comparison
            return f"""## 评估任务（知识库题目 — RAG混合评估模式）

## 题目
{current_question.get('question_text', '')}

## AI参考答案（评分基准）
{ai_ref if ai_ref else '标准答案暂未提供，请根据你的专业知识评分'}

## 候选人回答
{transcript[:3000] if transcript else '（候选人未作答）'}

## 评估步骤
1. 如果题目有AI参考答案，以它为基准进行评分
2. 如果需要更多参考，使用 retrieve_reference_answer 工具检索知识库
3. 对比候选人的回答与参考答案，找出覆盖点和遗漏点
4. 给出综合评分和详细评语"""
        else:
            # Resume mode: focus on resume consistency + 4-dimension scoring
            import json
            parsed = resume_ocr.get("parsed", {}) or {}
            skills = parsed.get("skills", [])
            experiences = parsed.get("experience", [])

            return f"""## 评估任务（简历题目 — LLM-as-a-Judge模式）

## 题目
{current_question.get('question_text', '')}

## 题目相关的简历上下文
{current_question.get('source_resume_context', '无')[:1000]}

## AI参考答案（仅供参考）
{ai_ref[:500] if ai_ref else '无参考答案'}

## 候选人回答
{transcript[:3000] if transcript else '（候选人未作答）'}

## 简历信息（供真实性验证）
候选人的技能: {json.dumps(skills, ensure_ascii=False)}
候选人的经历数量: {len(experiences)}
{chr(10).join(f"- {e.get('company', '')}: {e.get('position', '')} ({e.get('description', '')[:100]})" for e in experiences[:5])}

## 评估步骤
1. 如果需要验证回答与简历的一致性，使用 check_resume_consistency 工具
2. 注意：**不要去检索知识库**，这是简历题，知识库中没有相关内容
3. 从真实性、完整性、清晰度、技术深度四个维度评分
4. 给出综合评分和详细评语"""

    def parse_output(self, content: str) -> Dict[str, Any]:
        analysis = parse_json_response(content)

        if "error" in analysis:
            raw = analysis.get("raw", content)
            logger.warning(
                f"AnswerEvaluator({self.eval_mode}) JSON parse failed, "
                f"attempting best-effort extraction ({len(content)} chars)"
            )
            return _best_effort_parse(raw, self.eval_mode)

        # --- Normal path: clean JSON was parsed ---
        analysis.setdefault("eval_mode", self.eval_mode)

        # 仅 LLM Judge 模式扁平化四维评分；RAG 模式不需要这些字段
        if self.eval_mode == "llm_judge":
            accuracy = analysis.pop("accuracy", {})
            completeness = analysis.pop("completeness", {})
            clarity = analysis.pop("clarity", {})
            technical_depth = analysis.pop("technical_depth", {})

            analysis["accuracy_score"] = accuracy.get("score", 0) if isinstance(accuracy, dict) else 0
            analysis["accuracy_reasoning"] = accuracy.get("reasoning", "") if isinstance(accuracy, dict) else ""
            analysis["completeness_score"] = completeness.get("score", 0) if isinstance(completeness, dict) else 0
            analysis["completeness_reasoning"] = completeness.get("reasoning", "") if isinstance(completeness, dict) else ""
            analysis["clarity_score"] = clarity.get("score", 0) if isinstance(clarity, dict) else 0
            analysis["clarity_reasoning"] = clarity.get("reasoning", "") if isinstance(clarity, dict) else ""
            analysis["technical_depth_score"] = technical_depth.get("score", 0) if isinstance(technical_depth, dict) else 0
            analysis["technical_depth_reasoning"] = technical_depth.get("reasoning", "") if isinstance(technical_depth, dict) else ""

        logger.info(
            f"AnswerEvaluator({self.eval_mode}): "
            f"overall_score={analysis.get('overall_score', 'N/A')}"
        )
        return {"answer_analyses": [analysis]}


# ---- Best-effort extraction helpers ----

def _extract_dim_score(text: str, label_pattern: str, default: int = 1) -> int:
    """Extract a dimension score from text in various formats.

    Handles:
      - JSON: "accuracy": {"score": 4}
      - Pipe table: | **真实性 (Accuracy)** | 1/5 | ... |
      - Key-value: accuracy: 3
    """
    import re

    # JSON-style: "accuracy": {"score": 4}
    m = re.search(rf'"{label_pattern}"\s*:\s*\{{\s*"score"\s*:\s*(\d+)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Pipe table: | **真实性 (Accuracy)** | 1/5 | ... |
    m = re.search(rf'\|\s*\*?\*?{label_pattern}[^|]*\*?\*?\s*\|\s*(\d+)\s*/?\d*\s*\|', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Simple key-value: accuracy: 3  or  准确性=3
    m = re.search(rf'{label_pattern}\s*[：:＝=]\s*(\d+)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    return default


def _extract_list(text: str, labels: list) -> list:
    """Extract a list of strings from JSON arrays, markdown lists, or numbered lists."""
    import re

    for label in labels:
        # JSON array: "strengths": ["a", "b"]
        m = re.search(rf'"{label}"\s*:\s*\[(.*?)\]', text, re.DOTALL | re.IGNORECASE)
        if m:
            items = re.findall(r'"([^"]+)"', m.group(1))
            if items:
                return items

        # Numbered list after label: **遗漏点**:\n1. item\n2. item
        section_m = re.search(
            rf'{label}[^\n]*\n((?:\s*\d+\.\s*.+(?:\n|$))+)',
            text, re.IGNORECASE
        )
        if section_m:
            items = re.findall(r'\d+\.\s*(.+?)(?:\n|$)', section_m.group(1))
            if items:
                return [i.strip() for i in items if i.strip()]

        # Dash/star list: - item1\n- item2
        section_m = re.search(
            rf'{label}[^\n]*\n((?:\s*[-*]\s*.+(?:\n|$))+)',
            text, re.IGNORECASE
        )
        if section_m:
            items = re.findall(r'[-*]\s*(.+?)(?:\n|$)', section_m.group(1))
            if items:
                return [i.strip() for i in items if i.strip()]

    return []


def _best_effort_parse(raw: str, eval_mode: str) -> dict:
    """Parse an LLM output that failed JSON parsing, handling ALL known formats.

    Handles:
      1. Pure JSON with extra text before/after
      2. Markdown pipe tables: | **维度** | score | reasoning |
      3. Bold-label format: **综合评分**: 5/100
      4. Mixed: JSON fragments embedded in markdown
    """
    import re
    is_kb = (eval_mode == "rag_hybrid")

    # --- 1. Extract overall score (most critical field) ---
    overall = 0.0
    # Patterns ordered by specificity — handles both "综合评分：80" and "**综合评分**: 5/100"
    pats = [
        r'(?:\*{0,2})综合评分(?:\*{0,2})\s*[：:]\s*(\d+(?:\.\d+)?)\s*/\s*100',
        r'(?:\*{0,2})综合评分(?:\*{0,2})\s*[：:]\s*(\d+(?:\.\d+)?)',
        r'overall_score\s*[：:]\s*(\d+(?:\.\d+)?)',
        r'"overall_score"\s*:\s*(\d+(?:\.\d+)?)',
    ]
    for p in pats:
        m = re.search(p, raw)
        if m:
            overall = float(m.group(1))
            break

    # --- 2. Extract dimension scores ---
    acc = _extract_dim_score(raw, r'(?:真实性|accuracy)', 1)
    comp = _extract_dim_score(raw, r'(?:完整性|completeness)', 1)
    clar = _extract_dim_score(raw, r'(?:清晰度|clarity)', 1)
    tech = _extract_dim_score(raw, r'(?:技术深度|technical_depth)', 1)

    # --- 3. Extract authenticity_flag ---
    auth = "uncertain"
    for flag in ["consistent", "inconsistent"]:
        if re.search(rf'\b{flag}\b', raw, re.IGNORECASE):
            auth = "consistent" if flag == "consistent" else "inconsistent"
            break

    # --- 4. Extract assessment text ---
    assessment = raw[:500]
    for pat_label in ['assessment', '评语', '综合评价', '详细评价']:
        # Try: **评语**: text
        m = re.search(rf'{pat_label}[：:*\s]+(.+?)(?:\n\n|\n\*\*|\Z)', raw, re.DOTALL | re.IGNORECASE)
        if m:
            txt = m.group(1).strip()
            if len(txt) > 20:
                assessment = txt[:500]
                break

    # --- 5. Extract lists ---
    strengths = _extract_list(raw, ['strengths', '优势', '优点', '亮点'])
    improvements = _extract_list(raw, ['areas_for_improvement', '改进建议', '改进', '待提升', '待改进'])
    covered = _extract_list(raw, ['covered_points', '覆盖', '得分点覆盖'])
    missing = _extract_list(raw, ['missing_points', '遗漏', '遗漏点'])

    # --- 6. Build result ---
    result = {
        "eval_mode": eval_mode,
        "overall_score": overall,
        "assessment": assessment,
        "strengths": strengths,
        "authenticity_flag": auth,
    }

    if is_kb:
        result.update({
            "vector_similarity": 0.0,
            "covered_points": covered,
            "missing_points": missing or ["请提供更详细的回答以便评估"],
            "areas_for_improvement": improvements or (["请提供更详细的回答以便评估"] if not missing else []),
        })
    else:
        result.update({
            "accuracy_score": acc,
            "accuracy_reasoning": "",
            "completeness_score": comp,
            "completeness_reasoning": "",
            "clarity_score": clar,
            "clarity_reasoning": "",
            "technical_depth_score": tech,
            "technical_depth_reasoning": "",
            "areas_for_improvement": improvements or (["请提供更详细的回答以便评估"] if overall < 30 else []),
        })

    return {"answer_analyses": [result]}
