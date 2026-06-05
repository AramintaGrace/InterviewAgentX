"""Routing node for conditional edges in the interview graph.

Supports two routing modes:
  1. Orchestrator-driven (multi_agent_enabled=True): Reads the
     orchestrator_decision from state for dynamic routing.
  2. Rule-based (default): Original linear progression logic.

The orchestrator can decide to inject follow-up questions, adjust
difficulty, or route to error handling — not just linear progression.
"""

import logging
from typing import Literal

from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


def route_after_answer_analysis(
    state: InterviewState,
) -> Literal["next_question", "generate_report", "end"]:
    """Determine the next step after analyzing an answer.

    Orchestrator mode: reads orchestrator_decision for dynamic routing.
    Rule-based mode: original linear progression.

    - If more questions remain: route to next_question
    - If all questions answered: route to generate_report
    - If errors occurred: route to end (graceful termination)
    - If orchestrator requested follow-up: route to next_question
    """
    settings = get_settings()

    # Check for orchestrator decision (multi-agent mode)
    orchestrator_decision = state.get("orchestrator_decision", {}) or {}
    if settings.multi_agent_enabled and orchestrator_decision:
        action = orchestrator_decision.get("next_action", "")
        if action == "next_question":
            return "next_question"
        elif action == "generate_report":
            return "generate_report"
        elif action == "end":
            return "end"
        elif action == "follow_up":
            logger.info("Orchestrator requested follow-up question")
            return "next_question"

    # Rule-based routing (original logic)
    question_index = state.get("question_index", 0)
    total_questions = state.get("total_questions", 0)
    errors = state.get("errors", [])

    # Check for critical errors
    critical_errors = [e for e in errors if e.get("phase") == "answer_analysis"]
    if len(critical_errors) >= 3:
        logger.warning(f"Too many errors ({len(critical_errors)}), ending interview")
        return "end"

    # Check for pending follow-ups (multi-agent feature)
    pending_follow_ups = state.get("pending_follow_ups", [])
    if pending_follow_ups:
        logger.info(f"Processing {len(pending_follow_ups)} pending follow-up(s)")
        return "next_question"

    # Advance to next question or generate report
    if question_index + 1 < total_questions:
        logger.info(f"Moving to question {question_index + 2}/{total_questions}")
        return "next_question"
    else:
        logger.info("All questions answered, generating report")
        return "generate_report"


def route_question_generation(
    state: InterviewState,
) -> Literal["answering", "end"]:
    """Route after question generation.

    If questions were generated successfully, proceed to answering.
    Otherwise, end the workflow.
    """
    questions = state.get("questions", [])
    if questions:
        return "answering"

    logger.error("No questions generated")
    return "end"
