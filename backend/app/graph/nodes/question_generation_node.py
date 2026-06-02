"""Question Generation graph node."""

import json
import logging
import time
import uuid
from typing import Any, Dict

from app.agents.agent_factory import create_deepseek_llm
from app.agents.prompts.question_generation import (
    RESUME_QUESTION_PROMPT,
    KB_QUESTION_PROMPT,
    MIXED_QUESTION_PROMPT,
)
from app.agents.structured_output import parse_json_response
from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


async def generate_questions_node(state: InterviewState) -> Dict[str, Any]:
    """Generate interview questions based on the configured question source.

    Supports three modes:
    - resume: Generate from resume experiences and projects
    - knowledge_base: Select from knowledge base items
    - mixed: Mix of both sources
    """
    settings = get_settings()
    llm = create_deepseek_llm(settings, temperature=0.5)

    question_source = state.get("question_source", "resume")
    total_questions = state.get("total_questions", 5)

    try:
        if question_source == "resume":
            questions = await _generate_from_resume(state, llm, total_questions)
        elif question_source == "knowledge_base":
            questions = await _generate_from_kb(state, llm, total_questions)
        else:
            questions = await _generate_mixed(state, llm, total_questions)

        # Assign IDs and order
        for i, q in enumerate(questions):
            q["question_id"] = str(uuid.uuid4())
            q["question_order"] = i + 1

        logger.info(f"Generated {len(questions)} questions from source: {question_source}")

        return {
            "questions": questions,
            "question_index": 0,
            "current_phase": "answering",
        }
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        return {
            "errors": [{"phase": "question_generation", "error_message": str(e)}],
            "current_phase": "answering",
        }


async def _generate_from_resume(
    state: InterviewState, llm, count: int
) -> list[Dict[str, Any]]:
    """Generate questions based on resume experiences and projects."""
    resume_ocr = state.get("resume_ocr", {})
    resume_analyses = state.get("resume_analyses", [])

    resume_context = json.dumps(resume_ocr.get("parsed", {}), ensure_ascii=False)
    analysis_text = json.dumps(resume_analyses[-1] if resume_analyses else {}, ensure_ascii=False)

    prompt = RESUME_QUESTION_PROMPT.format(
        resume_context=resume_context[:4000],
        resume_analysis=analysis_text[:2000],
        count=count,
    )

    response = await llm.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    return parse_json_response(content) if isinstance(parse_json_response(content), list) else []


async def _generate_from_kb(
    state: InterviewState, llm, count: int
) -> list[Dict[str, Any]]:
    """Select questions from knowledge base items."""
    # KB items are passed through state or retrieved from service
    # For now, generate basic structure
    kb_context = json.dumps(state.get("knowledge_base_items", []), ensure_ascii=False)

    prompt = KB_QUESTION_PROMPT.format(
        knowledge_base_items=kb_context[:4000],
        count=count,
    )

    response = await llm.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    return parse_json_response(content) if isinstance(parse_json_response(content), list) else []


async def _generate_mixed(
    state: InterviewState, llm, count: int
) -> list[Dict[str, Any]]:
    """Generate a mix of resume-based and knowledge-base questions."""
    resume_ocr = state.get("resume_ocr", {})
    resume_analyses = state.get("resume_analyses", [])

    resume_context = json.dumps(resume_ocr.get("parsed", {}), ensure_ascii=False)
    analysis_text = json.dumps(resume_analyses[-1] if resume_analyses else {}, ensure_ascii=False)
    kb_context = json.dumps(state.get("knowledge_base_items", []), ensure_ascii=False)

    prompt = MIXED_QUESTION_PROMPT.format(
        resume_context=resume_context[:3000],
        resume_analysis=analysis_text[:1500],
        knowledge_base_items=kb_context[:2000],
        count=count,
    )

    response = await llm.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    return parse_json_response(content) if isinstance(parse_json_response(content), list) else []
