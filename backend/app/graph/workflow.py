"""LangGraph workflow builder for the interview process.

Supports two modes controlled by settings.multi_agent_enabled:

  Single-agent mode (default, backward compatible):
    Linear pipeline with 5 hardcoded nodes:
      START → resume_analysis → generate_questions → process_answer
            → analyze_answer → generate_report → END

  Multi-agent mode (multi_agent_enabled=True):
    Orchestrator-driven graph with autonomous agents:
      START → orchestrator → [ResumeAnalyst | QuestionCurator |
                              AnswerEvaluator | ReportSynthesizer] → orchestrator → END
    The orchestrator dynamically routes between agents based on
    interview state, answer quality, and error conditions.
"""

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, START, END

from app.config import get_settings
from app.graph.checkpointer import get_checkpointer
from app.graph.state import InterviewState
from app.graph.nodes.resume_analysis_node import resume_analysis_node
from app.graph.nodes.question_generation_node import generate_questions_node
from app.graph.nodes.answer_analysis_node import analyze_single_answer_node
from app.graph.nodes.report_generation_node import generate_report_node
from app.graph.nodes.orchestrator_node import orchestrator_node
from app.graph.nodes.routing_node import (
    route_after_answer_analysis,
    route_question_generation,
)

logger = logging.getLogger(__name__)

# Cached compiled graph
_compiled_graph: Optional[StateGraph] = None


def build_interview_graph() -> StateGraph:
    """Build the complete interview workflow graph.

    In single-agent mode: the graph topology IS the coordinator
    (no separate coordinator agent). Linear flows use hardcoded
    edges; dynamic decisions use conditional_edges.

    In multi-agent mode: the orchestrator node makes autonomous
    routing decisions between specialized agents.
    """
    settings = get_settings()
    builder = StateGraph(InterviewState)

    # Register nodes (always available, feature flag controls behavior)
    builder.add_node("resume_analysis", resume_analysis_node)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("process_current_answer", process_answer_node)
    builder.add_node("analyze_current_answer", analyze_single_answer_node)
    builder.add_node("generate_report", generate_report_node)

    if settings.multi_agent_enabled:
        # ---- Multi-agent mode: orchestrator-driven routing ----
        builder.add_node("orchestrator", orchestrator_node)

        # Orchestrator is the entry point
        builder.add_edge(START, "orchestrator")

        # Orchestrator routes to specialized agents
        builder.add_conditional_edges(
            "orchestrator",
            _route_orchestrator,
            {
                "resume_analysis": "resume_analysis",
                "generate_questions": "generate_questions",
                "process_answer": "process_current_answer",
                "analyze_answer": "analyze_current_answer",
                "generate_report": "generate_report",
                "end": END,
            },
        )

        # Each agent returns to orchestrator for next decision
        builder.add_edge("resume_analysis", "orchestrator")
        builder.add_edge("generate_questions", "orchestrator")
        builder.add_edge("process_current_answer", "orchestrator")
        builder.add_edge("analyze_current_answer", "orchestrator")
        builder.add_edge("generate_report", "orchestrator")

        logger.info("Interview graph built in MULTI-AGENT mode (orchestrator-driven)")
    else:
        # ---- Single-agent mode: original linear pipeline ----
        builder.add_edge(START, "resume_analysis")
        builder.add_edge("resume_analysis", "generate_questions")

        builder.add_conditional_edges(
            "generate_questions",
            route_question_generation,
            {
                "answering": "process_current_answer",
                "end": END,
            },
        )

        builder.add_edge("process_current_answer", "analyze_current_answer")

        builder.add_conditional_edges(
            "analyze_current_answer",
            route_after_answer_analysis,
            {
                "next_question": "process_current_answer",
                "generate_report": "generate_report",
                "end": END,
            },
        )

        builder.add_edge("generate_report", END)

        logger.info("Interview graph built in SINGLE-AGENT mode (linear pipeline)")

    return builder


def _route_orchestrator(state: InterviewState) -> str:
    """Route from orchestrator to the next specialized agent.

    Reads the orchestrator_decision from state to determine routing.
    Falls back to linear progression if no decision is available.

    Returns one of: resume_analysis, generate_questions, process_answer,
                   analyze_answer, generate_report, end
    """
    decision = state.get("orchestrator_decision", {}) or {}
    action = decision.get("next_action", "")

    # Map orchestrator actions to node names
    action_map = {
        "resume_analysis": "resume_analysis",
        "generate_questions": "generate_questions",
        "wait_for_answer": "process_answer",
        "process_answer": "process_answer",
        "answer_analysis": "analyze_answer",
        "analyze_answer": "analyze_answer",
        "report_generation": "generate_report",
        "generate_report": "generate_report",
        "end": "end",
    }

    mapped = action_map.get(action, "")
    if mapped:
        logger.info(f"Orchestrator routes to: {mapped} (action='{action}')")
        return mapped

    # Fallback: linear progression based on phase
    phase = state.get("current_phase", "init")
    fallback_map = {
        "init": "resume_analysis",
        "resume_upload": "resume_analysis",
        "resume_analysis": "resume_analysis",
        "question_generation": "generate_questions",
        "answering": "process_answer",
        "answer_analysis": "analyze_answer",
        "report_generation": "generate_report",
        "completed": "end",
    }
    fallback = fallback_map.get(phase, "end")
    logger.warning(
        f"Orchestrator fallback: phase='{phase}' → {fallback} "
        f"(no valid decision, action='{action}')"
    )
    return fallback


async def process_answer_node(state: InterviewState) -> dict:
    """Node that processes the current answer.

    In the HITL (Human-in-the-Loop) pattern, this node is reached
    when the frontend submits an answer. The answer data is already
    in the state (appended via answers list), so we just advance the index.

    In multi-agent mode: the orchestrator can dynamically add follow-up
    questions or adjust difficulty based on answer quality analysis.
    """
    question_index = state.get("question_index", 0)
    questions = state.get("questions", [])
    answers = state.get("answers", [])

    new_index = len(answers) - 1 if answers else question_index

    logger.info(f"Processing answer for question {new_index + 1}/{len(questions)}")

    return {
        "question_index": new_index,
        "current_phase": "answering",
    }


async def get_interview_graph():
    """Get or create the compiled interview graph with checkpointer.

    The graph is compiled once and cached. When multi_agent_enabled
    is toggled, the cache is invalidated and rebuilt.
    """
    global _compiled_graph

    if _compiled_graph is not None:
        return _compiled_graph

    settings = get_settings()
    checkpointer = await get_checkpointer(settings)

    builder = build_interview_graph()
    _compiled_graph = builder.compile(checkpointer=checkpointer)

    mode = "multi-agent" if settings.multi_agent_enabled else "single-agent"
    logger.info(f"Interview graph compiled with PostgreSQL checkpointer ({mode} mode)")
    return _compiled_graph
