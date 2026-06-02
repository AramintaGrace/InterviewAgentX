"""Routing node for conditional edges in the interview graph."""

import logging
from typing import Literal

from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


def route_after_answer_analysis(
    state: InterviewState,
) -> Literal["next_question", "generate_report", "end"]:
    """Determine the next step after analyzing an answer.

    - If more questions remain: route to next_question
    - If all questions answered: route to generate_report
    - If errors occurred: route to end (graceful termination)
    """
    question_index = state.get("question_index", 0)
    total_questions = state.get("total_questions", 0)
    errors = state.get("errors", [])

    # Check for critical errors
    critical_errors = [e for e in errors if e.get("phase") == "answer_analysis"]
    if len(critical_errors) >= 3:
        logger.warning(f"Too many errors ({len(critical_errors)}), ending interview")
        return "end"

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
