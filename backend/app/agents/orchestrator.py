"""InterviewOrchestratorAgent — master coordinator for the multi-agent system.

Extends BaseAgent with tools for:
  - Reading compact interview state summary
  - Evaluating answer quality for follow-up decisions
  - Dynamically adjusting interview difficulty

This agent replaces the hardcoded conditional edges in workflow.py
with autonomous decision-making. Instead of fixed routing rules,
the orchestrator examines the full state and decides the next action.

Key capabilities:
  - Dynamic agent routing based on interview phase and state
  - Follow-up question decisions based on answer quality
  - Adaptive difficulty adjustment
  - Error recovery and graceful degradation
"""

import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent
from app.agents.structured_output import parse_json_response
from app.agents.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class InterviewOrchestratorAgent(BaseAgent):
    """Master coordinator agent for the multi-agent interview system.

    Capabilities:
      - Reads interview state summary (tool: get_state_summary)
      - Evaluates answer quality for follow-up (tool: check_answer_quality)
      - Adjusts difficulty dynamically (tool: adjust_difficulty)

    Makes autonomous routing decisions:
      - Which specialized agent to invoke next
      - Whether to add follow-up questions
      - When to end the interview and generate report
      - How to handle errors

    Output: Orchestrator decision dict merged into state.
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
            name="InterviewOrchestrator",
        )

    @property
    def system_prompt(self) -> str:
        return ORCHESTRATOR_SYSTEM_PROMPT

    def build_user_message(self, state: Dict[str, Any]) -> str:
        current_phase = state.get("current_phase", "init")
        question_index = state.get("question_index", 0)
        total_questions = state.get("total_questions", 0)
        question_source = state.get("question_source", "resume")
        answers = state.get("answers", [])
        answer_analyses = state.get("answer_analyses", [])
        errors = state.get("errors", [])

        return f"""## 当前面试状态

- 阶段: {current_phase}
- 题目来源: {question_source}
- 题目进度: {question_index + 1}/{total_questions}
- 已提交答案: {len(answers)}
- 已完成分析: {len(answer_analyses)}
- 错误数: {len(errors)}
- 简历已分析: {bool(state.get('resume_analyses'))}
- 题目已生成: {bool(state.get('questions'))}

## 你需要做什么
1. 如果需要更多状态信息，使用get_state_summary工具
2. 如果需要检查某个答案的质量，使用check_answer_quality工具
3. 根据当前阶段和状态，决定下一步操作

请分析当前状态并返回路由决策JSON。"""

    def parse_output(self, content: str) -> Dict[str, Any]:
        decision = parse_json_response(content)

        if "error" in decision:
            logger.warning(f"Orchestrator parse error: {decision['error']}")
            # Graceful fallback: default to linear progression
            return {
                "orchestrator_decision": {
                    "next_action": "continue",
                    "phase": "unknown",
                    "reasoning": "Parse error, defaulting to linear progression",
                    "params": {},
                }
            }

        next_action = decision.get("next_action", "continue")
        phase = decision.get("phase", "unknown")
        reasoning = decision.get("reasoning", "")

        logger.info(
            f"Orchestrator decision: action={next_action}, "
            f"phase={phase}, reasoning='{reasoning[:80]}...'"
        )

        # Route the orchestrator's decision to specific state updates
        params = decision.get("params", {})
        state_updates: Dict[str, Any] = {
            "orchestrator_decision": decision,
        }

        # Handle difficulty adjustment
        if params.get("difficulty_adjustment"):
            state_updates["interview_difficulty"] = params["difficulty_adjustment"]

        # Handle follow-up requests
        if params.get("follow_up_needed"):
            state_updates["pending_follow_ups"] = [{
                "reason": params.get("follow_up_reason", ""),
                "suggested_topic": params.get("follow_up_topic", ""),
            }]

        return state_updates
