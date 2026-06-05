"""ResumeAnalystAgent — autonomous resume analysis with tool-calling capability.

Extends BaseAgent with tools for:
  - Reading full OCR text from state
  - Querying candidate history from DB
  - Flagging inconsistencies for follow-up questioning

Unlike the current resume_analysis_node which just calls llm.ainvoke(prompt),
this agent can autonomously decide to:
  - Read additional resume sections if the initial text is insufficient
  - Check candidate history for patterns from past interviews
  - Flag specific claims for verification during the interview
"""

import json
import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent
from app.agents.structured_output import parse_json_response
from app.agents.prompts.resume_analysis import RESUME_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class ResumeAnalystAgent(BaseAgent):
    """Autonomous agent for deep resume analysis.

    Capabilities:
      - Reads full OCR text (tool: get_full_resume_text)
      - Queries candidate history for patterns (tool: query_candidate_history)
      - Flags inconsistencies for interview follow-up (tool: flag_inconsistency)

    Output: ResumeAnalysisOutput merged into state.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        max_iterations: int = 3,
    ):
        super().__init__(
            llm=llm,
            tools=tools,
            max_iterations=max_iterations,
            name="ResumeAnalyst",
        )

    @property
    def system_prompt(self) -> str:
        return """你是一个专业的简历分析Agent。你的任务是对候选人简历进行深度分析。

## 你可以使用的工具
- get_full_resume_text: 获取完整的简历OCR文本和结构化解析数据
- query_candidate_history: 查询候选人的历史面试记录
- flag_inconsistency: 标记简历中的不一致或需要追问的地方

## 工作流程
1. 首先获取完整简历文本
2. 如果存在候选人历史记录，查询并参考
3. 对简历进行全面分析
4. 如有不一致或疑点，标记flag
5. 生成结构化的分析报告

## 分析维度
1. **综合评估** (overall_assessment): 对候选人整体素质的简要评价
2. **优势** (strengths): 候选人突出的优势，至少3条
3. **不足之处** (weaknesses): 简历中体现的短板或风险点
4. **技能匹配度** (skill_match): 关键技能的掌握程度评分(1-10)
5. **经验相关度** (experience_relevance_score): 整体经验匹配度(1-100)
6. **项目亮点** (project_highlights): 值得深入询问的项目经历
7. **建议面试题目** (suggested_questions): 基于简历提出的面试问题，至少5题
8. **风险提示** (red_flags): 需要面试中特别关注的疑点

## 最终输出格式
当你完成分析后，输出以下JSON（不要包含markdown代码块标记）：
{
  "overall_assessment": "综合评价...",
  "strengths": ["优势1", "优势2", "优势3"],
  "weaknesses": ["不足1", "不足2"],
  "skill_match": {"Python": 8, "FastAPI": 7},
  "experience_relevance_score": 75,
  "project_highlights": [
    {"project": "项目名称", "depth_analysis": "值得深挖的方向"}
  ],
  "suggested_questions": ["问题1", "问题2", "问题3", "问题4", "问题5"],
  "red_flags": ["需要关注的疑点"]
}
"""

    def build_user_message(self, state: Dict[str, Any]) -> str:
        resume_ocr = state.get("resume_ocr", {}) or {}
        resume_text = resume_ocr.get("raw_text", "")
        parsed = resume_ocr.get("parsed", {}) or {}

        return f"""请分析以下候选人的简历。

## 候选人ID
{state.get("candidate_id", "未知")}

## 简历文件名
{resume_ocr.get("file_name", "未知")}

## 简历文本预览（前2000字符）
{resume_text[:2000]}

## 结构化解析数据
{json.dumps(parsed, ensure_ascii=False, default=str)[:1500]}

请使用你的工具获取更多信息，然后进行全面分析。"""

    def parse_output(self, content: str) -> Dict[str, Any]:
        analysis = parse_json_response(content)
        if "error" in analysis:
            logger.warning(f"ResumeAnalyst produced invalid output: {analysis['error']}")
            return {
                "resume_analyses": [],
                "errors": [{"phase": "resume_analysis", "error_message": str(analysis.get("raw", ""))[:200]}],
            }

        # Add metadata
        resume_ocr = {}
        # We don't have state here, but the caller will merge

        logger.info(
            f"ResumeAnalyst completed: score={analysis.get('experience_relevance_score', 'N/A')}, "
            f"strengths={len(analysis.get('strengths', []))}, "
            f"red_flags={len(analysis.get('red_flags', []))}"
        )
        return {"resume_analyses": [analysis]}
