"""QuestionCuratorAgent — dynamic question generation with Agentic RAG.

Extends BaseAgent with Agentic RAG tools for:
  - Searching knowledge base with autonomous retrieval decisions
  - Reading resume analysis for personalized questions
  - Listing KB categories for targeted question selection

Key difference from current pipeline: this agent autonomously decides
WHETHER to search the KB, formulates optimal queries, evaluates
result relevance, and re-searches if quality is low — true agentic RAG.
"""

import json
import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent
from app.agents.structured_output import parse_json_response

logger = logging.getLogger(__name__)


class QuestionCuratorAgent(BaseAgent):
    """Autonomous agent for interview question generation with Agentic RAG.

    Capabilities:
      - Agentic RAG search for KB questions (tool: search_knowledge_base)
      - Reads resume analysis for context (tool: get_resume_analysis)
      - Lists available KB categories (tool: get_kb_categories)

    Supports three generation modes:
      - resume: Questions from candidate experiences and projects
      - knowledge_base: Questions selected from KB with agentic retrieval
      - mixed: Hybrid of both with configurable ratio

    Output: list[GeneratedQuestion] merged into state.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        max_iterations: int = 5,
    ):
        super().__init__(
            llm=llm,
            tools=tools,
            max_iterations=max_iterations,
            name="QuestionCurator",
        )

    @property
    def system_prompt(self) -> str:
        return """你是一个专业的面试题目策展Agent。你的任务是根据简历和知识库生成个性化的面试题目。

## 你可以使用的工具
- search_knowledge_base: 使用Agentic RAG从知识库检索题目（支持自动查询优化和相关性评估）
- get_resume_analysis: 获取简历分析结果（优势、劣势、技能评分等）
- get_kb_categories: 获取可用的知识库分类列表

## Agentic RAG使用指南
search_knowledge_base工具具备智能检索能力：
1. 它会自动判断是否需要从知识库检索
2. 自动优化检索查询词
3. 评估检索结果的相关性
4. 如果相关性低，会自动重新检索
5. 返回带引用的结果

你应该：
- 对于知识库和混合模式，主动使用search_knowledge_base
- 如果检索结果相关性低，尝试用不同的关键词重新检索
- 根据简历分析中的weaknesses和red_flags，有针对性地搜索相关题目

## 题目生成模式

### 简历模式 (source: resume)
- 基于简历中的工作经历和项目经历生成题目
- 包含STAR行为面试题和技术深挖题
- 难度递进
- source_type: "resume_experience" 或 "resume_project"

### 知识库模式 (source: knowledge_base)
- 从知识库中选取合适的题目
- 使用search_knowledge_base检索相关题目
- 将KB条目的问题作为question_text，答案作为ai_reference_answer
- source_type: "knowledge_base"

### 混合模式 (source: mixed)
- 结合简历题和知识库题
- 按配置的比例混合
- 交错排列

## 最终输出格式
当你完成题目生成后，输出以下JSON数组：
[
  {
    "source_type": "resume_experience | resume_project | knowledge_base",
    "source_resume_context": "简历中相关的经历片段（简历题必填）",
    "source_kb_item_id": "知识库条目UUID（知识库题必填）",
    "question_text": "完整的面试问题",
    "ai_reference_answer": "参考答案或关键要点"
  }
]

## 注意事项
- 题目数量严格按要求生成
- 确保题目的source_type正确标注
- 知识库题目的source_kb_item_id必须与检索结果中的ID完全匹配
- 题目难度应该递进排列
"""

    def build_user_message(self, state: Dict[str, Any]) -> str:
        question_source = state.get("question_source", "resume")
        total_questions = state.get("total_questions", 5)
        resume_ocr = state.get("resume_ocr", {}) or {}
        questions = state.get("questions", [])

        # Build context message
        parts = [
            f"## 题目生成任务",
            f"- 题目来源模式: {question_source}",
            f"- 需要生成数量: {total_questions}",
            f"- 已生成数量: {len(questions)}",
        ]

        if resume_ocr:
            parsed = resume_ocr.get("parsed", {}) or {}
            parts.append(f"\n## 候选人信息")
            parts.append(f"- 姓名: {parsed.get('name', '未知')}")
            parts.append(f"- 技能: {parsed.get('skills', [])}")
            parts.append(f"- 经历数量: {len(parsed.get('experience', []))}")

        # Check for KB configs (for knowledge_base and mixed modes)
        kb_configs = state.get("kb_configs", [])
        pool_ids = state.get("pool_ids", [])
        if kb_configs or pool_ids:
            parts.append(f"\n## 知识库配置")
            if kb_configs:
                parts.append(f"- 分类配置: {json.dumps(kb_configs, ensure_ascii=False)}")
            if pool_ids:
                parts.append(f"- 必选题目池: {len(pool_ids)} 道题目")

        return "\n".join(parts)

    def parse_output(self, content: str) -> Dict[str, Any]:
        questions = parse_json_response(content)

        if isinstance(questions, dict):
            # Might be wrapped in a key
            for key in ["questions", "data", "result"]:
                if key in questions:
                    questions = questions[key]
                    break
            if isinstance(questions, dict):
                logger.warning("QuestionCurator produced dict instead of list")
                questions = []

        if not isinstance(questions, list):
            logger.warning(
                f"QuestionCurator produced non-list output: {type(questions)}"
            )
            return {
                "questions": [],
                "errors": [{
                    "phase": "question_generation",
                    "error_message": "Agent did not produce a valid question list",
                }],
            }

        logger.info(
            f"QuestionCurator generated {len(questions)} questions"
        )
        return {"questions": questions}
