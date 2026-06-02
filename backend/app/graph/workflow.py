"""LangGraph workflow builder for the interview process.

Graph topology (nodes + edges):

                    START
                      │
                      v
            ┌──────────────────┐
            │  resume_analysis │  ← Node: Pass OCR data to Resume Analysis Agent
            └────────┬─────────┘
                      │
                      v
            ┌──────────────────────┐
            │  generate_questions  │  ← Node: Generate questions based on source mode
            └──────────┬───────────┘
                      │
                      v
            ┌──────────────────────────┐
            │  process_current_answer  │  ← Node: Wait for answer (HITL)
            │    (receives transcript   │        ┌─────────────────────┐
            │     from frontend)        │        │                     │
            └──────────┬───────────────┘        │  ┌──── WAIT ────┐  │
                      │                         │  │ 前端 POST     │  │
                      v                         │  │ answer data  │  │
            ┌──────────────────────────┐        │  └──────────────┘  │
            │  analyze_current_answer  │  ←─────┘  resume execution  │
            │  (routes by eval_mode)   │
            └──────────┬───────────────┘
                      │
                      v
            ┌──────────────────────────┐
            │  route_after_answer      │  ← conditional_edge:
            │  _analysis               │      - more questions → process_current_answer
            └──────┬──────────┬────────┘      - all done → generate_report
                   │          │
      more Qs ────┘          └──── all done ────┐
                                                 │
                                                 v
                                       ┌──────────────────┐
                                       │  generate_report │ ← Node: Read answer_analyses
                                       └────────┬─────────┘    summaries → generate report
                                                 │
                                                 v
                                                END
"""

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, START, END

from app.graph.checkpointer import get_checkpointer
from app.graph.state import InterviewState
from app.graph.nodes.resume_analysis_node import resume_analysis_node
from app.graph.nodes.question_generation_node import generate_questions_node
from app.graph.nodes.answer_analysis_node import analyze_single_answer_node
from app.graph.nodes.report_generation_node import generate_report_node
from app.graph.nodes.routing_node import (
    route_after_answer_analysis,
    route_question_generation,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

# Cached compiled graph
_compiled_graph: Optional[StateGraph] = None


def build_interview_graph() -> StateGraph:
    """Build the complete interview workflow graph.

    The graph topology IS the coordinator — no separate "coordinator agent".
    Linear flows use hardcoded edges; dynamic decisions use conditional_edges.
    """
    builder = StateGraph(InterviewState)

    # Register nodes
    builder.add_node("resume_analysis", resume_analysis_node)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("process_current_answer", process_answer_node)
    builder.add_node("analyze_current_answer", analyze_single_answer_node)
    builder.add_node("generate_report", generate_report_node)

    # Hardcoded edges for linear flows
    builder.add_edge(START, "resume_analysis")
    builder.add_edge("resume_analysis", "generate_questions")

    # Conditional: did question generation succeed?
    builder.add_conditional_edges(
        "generate_questions",
        route_question_generation,
        {
            "answering": "process_current_answer",
            "end": END,
        },
    )

    builder.add_edge("process_current_answer", "analyze_current_answer")

    # Conditional: more questions or generate report?
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

    return builder


async def process_answer_node(state: InterviewState) -> dict:
    """Node that processes the current answer.

    In the HITL (Human-in-the-Loop) pattern, this node is reached
    when the frontend submits an answer. The answer data is already
    in the state (appended via answers list), so we just advance the index.
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
    """Get or create the compiled interview graph with checkpointer."""
    global _compiled_graph

    if _compiled_graph is not None:
        return _compiled_graph

    settings = get_settings()
    checkpointer = await get_checkpointer(settings)

    builder = build_interview_graph()
    _compiled_graph = builder.compile(checkpointer=checkpointer)

    logger.info("Interview graph compiled with PostgreSQL checkpointer")
    return _compiled_graph
