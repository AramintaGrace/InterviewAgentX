"""Orchestrator graph node — calls InterviewOrchestratorAgent for dynamic routing.

This node replaces the hardcoded conditional edges in workflow.py with
autonomous decision-making. The orchestrator examines the full state
and decides which specialized agent to invoke next.

In single-agent mode (multi_agent_enabled=False), this node acts as a
pass-through that follows the original linear progression.
"""

import logging
from typing import Any, Dict

from app.agents.agent_factory import create_deepseek_llm
from app.agents.orchestrator import InterviewOrchestratorAgent
from app.agents.tools import create_orchestrator_tools
from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


async def orchestrator_node(state: InterviewState) -> Dict[str, Any]:
    """Master coordinator node — invokes the Orchestrator agent.

    In multi-agent mode: the orchestrator uses tools to inspect state
    and make an autonomous routing decision.

    In single-agent mode (default): follows the original linear
    progression based on current_phase.

    Args:
        state: Full InterviewState from LangGraph.

    Returns:
        Dict with orchestrator_decision and optional state updates
        (difficulty adjustment, follow-up requests).
    """
    settings = get_settings()

    if not settings.multi_agent_enabled:
        # Single-agent mode: linear progression based on phase
        return _linear_routing(state)

    # Multi-agent mode: autonomous decision via Orchestrator agent
    try:
        llm = create_deepseek_llm(settings, temperature=0.2)

        # Create tools with state provider
        tools = create_orchestrator_tools(state_provider=lambda: state)

        agent = InterviewOrchestratorAgent(
            llm=llm,
            tools=tools,
            max_iterations=settings.agent_max_iterations,
        )

        result = await agent.execute(state)
        logger.info(
            f"Orchestrator decision: {result.get('orchestrator_decision', {}).get('next_action', 'unknown')}"
        )
        return result

    except Exception as e:
        logger.error(f"Orchestrator agent failed: {e}", exc_info=True)
        # Graceful degradation: fall back to linear routing
        return _linear_routing(state)


def _linear_routing(state: InterviewState) -> Dict[str, Any]:
    """Original linear progression logic (single-agent mode fallback).

    Determines the next phase based on current state, replicating the
    original hardcoded edge logic from workflow.py.
    """
    current_phase = state.get("current_phase", "init")
    questions = state.get("questions", [])
    answers = state.get("answers", [])
    question_index = state.get("question_index", 0)
    total_questions = state.get("total_questions", 0)
    question_source = state.get("question_source", "resume")

    decision = {
        "next_action": "continue",
        "phase": current_phase,
        "reasoning": "Linear progression (single-agent mode)",
        "params": {},
    }

    if current_phase in ("init", "resume_upload", "resume_analysis"):
        decision["next_action"] = "resume_analysis"
    elif current_phase == "question_generation":
        decision["next_action"] = "generate_questions"
    elif current_phase == "answering":
        if question_index + 1 < total_questions:
            decision["next_action"] = "next_question"
        else:
            decision["next_action"] = "generate_report"
    elif current_phase == "answer_analysis":
        if question_index + 1 < total_questions:
            decision["next_action"] = "next_question"
        else:
            decision["next_action"] = "generate_report"
    elif current_phase == "report_generation":
        decision["next_action"] = "generate_report"
    elif current_phase == "completed":
        decision["next_action"] = "end"
    else:
        decision["next_action"] = "continue"

    return {"orchestrator_decision": decision}
