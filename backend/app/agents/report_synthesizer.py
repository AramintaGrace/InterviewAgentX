"""ReportSynthesizerAgent — holistic interview report generation.

Extends BaseAgent with tools for:
  - Collecting all answer analysis summaries
  - Computing aggregated dimension scores
  - Identifying patterns across answers

Uses DeepSeek Reasoner for deep analytical synthesis (the most
complex LLM call in the system).

Key difference from current pipeline: the agent can proactively
collect data, verify completeness, and request additional context
before generating the final report — rather than blindly formatting
a prompt with whatever data is in state.
"""

import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent
from app.agents.structured_output import parse_json_response

logger = logging.getLogger(__name__)


class ReportSynthesizerAgent(BaseAgent):
    """Autonomous agent for comprehensive interview report generation.

    Capabilities:
      - Collects all answer analyses (tool: collect_all_analyses)
      - Computes aggregated dimension scores (tool: compute_dimension_scores)
      - Uses DeepSeek Reasoner for deep analytical reasoning

    Output: InterviewReportOutput merged into state.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: List[BaseTool],
        max_iterations: int = 4,
    ):
        super().__init__(
            llm=llm,
            tools=tools,
            max_iterations=max_iterations,
            name="ReportSynthesizer",
        )

    @property
    def system_prompt(self) -> str:
        return """你是一个资深的面试评估报告生成Agent。你的任务是综合所有面试数据，生成一份全面的面试报告。

## 你可以使用的工具
- collect_all_analyses: 收集所有题目的答案分析摘要
- compute_dimension_scores: 计算各能力维度的聚合分数

## 工作流程
1. 调用collect_all_analyses获取每道题的评估摘要
2. 调用compute_dimension_scores获取维度聚合分数
3. 综合所有数据，生成结构化报告

## 报告内容要求

### 1. 总体评分 (overall_score, 0-100)
- 综合所有题目的表现
- 不是简单平均，需考虑题目难度和权重

### 2. 维度评分 (dimension_scores, 0-100)
- technical_ability: 技术能力
- communication: 沟通表达
- problem_solving: 问题解决能力
- experience_relevance: 经验匹配度
- cultural_fit: 文化契合度（如无法判断可为null）

### 3. 逐题回顾 (question_reviews)
每道题的简要评价：
- question_text: 题目文本
- source_type: 题目来源
- eval_mode: 评估模式
- score: 得分
- key_feedback: 关键反馈

### 4. 优势总结 (strengths)
候选人的核心优势和亮点

### 5. 待提升领域 (weaknesses)
需要改进的方面

### 6. 录用建议 (hiring_recommendation)
- strongly_recommend: 强烈推荐
- recommend: 推荐录用
- consider: 考虑录用
- not_recommend: 不予推荐

### 7. 详细评价 (detailed_feedback)
一段完整的综合评价文字（200-500字）

## 重要说明
- 你收到的数据是结构化的分析摘要，不是原始对话记录
- 基于这些数据生成报告，不要要求查看原始记录
- 报告需要客观、专业、有建设性

## 最终输出格式
{
  "overall_score": 82.5,
  "dimension_scores": {
    "technical_ability": 85,
    "communication": 78,
    "problem_solving": 80,
    "experience_relevance": 88,
    "cultural_fit": null
  },
  "question_reviews": [
    {
      "question_text": "...",
      "source_type": "resume_experience",
      "eval_mode": "llm_judge",
      "score": 85,
      "key_feedback": "简短的反馈"
    }
  ],
  "strengths": ["核心优势1", "核心优势2"],
  "weaknesses": ["待提升1"],
  "hiring_recommendation": "recommend",
  "detailed_feedback": "详细的综合评价文字..."
}
"""

    def build_user_message(self, state: Dict[str, Any]) -> str:
        import json

        resume_ocr = state.get("resume_ocr", {}) or {}
        parsed = resume_ocr.get("parsed", {}) or {}
        resume_analyses = state.get("resume_analyses", [])

        candidate_info = json.dumps({
            "name": parsed.get("name", "未知"),
            "current_role": parsed.get("current_role", ""),
            "skills": parsed.get("skills", []),
        }, ensure_ascii=False)

        last_analysis = resume_analyses[-1] if resume_analyses else {}
        resume_summary = json.dumps({
            "overall_assessment": last_analysis.get("overall_assessment", ""),
            "strengths": last_analysis.get("strengths", []),
            "weaknesses": last_analysis.get("weaknesses", []),
            "experience_relevance_score": last_analysis.get("experience_relevance_score", 0),
        }, ensure_ascii=False)

        return f"""## 报告生成任务

## 候选人信息
{candidate_info}

## 简历分析摘要
{resume_summary}

## 面试概况
- 会话ID: {state.get('session_id', '')}
- 题目总数: {state.get('total_questions', 0)}
- 已分析答案数: {len(state.get('answer_analyses', []))}

请使用collect_all_analyses和compute_dimension_scores工具获取详细数据，然后生成完整的面试报告。"""

    def parse_output(self, content: str) -> Dict[str, Any]:
        report = parse_json_response(content)

        if "error" in report:
            logger.warning(f"ReportSynthesizer parse error: {report['error']}")
            return {
                "errors": [{
                    "phase": "report_generation",
                    "error_message": str(report.get("raw", ""))[:200],
                }],
            }

        recommendation = report.get("hiring_recommendation", "consider")
        valid_recs = {"strongly_recommend", "recommend", "consider", "not_recommend"}
        if recommendation not in valid_recs:
            report["hiring_recommendation"] = "consider"

        logger.info(
            f"ReportSynthesizer completed: overall_score={report.get('overall_score', 'N/A')}, "
            f"recommendation={report.get('hiring_recommendation')}"
        )
        return {"interview_report": report}
