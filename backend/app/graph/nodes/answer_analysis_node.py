"""Answer Analysis graph node — fast single-shot LLM evaluation."""

import json
import logging
import time
from typing import Any, Dict, Optional

from app.agents.agent_factory import create_deepseek_llm
from app.agents.prompts.answer_analysis_kb import KB_ANSWER_ANALYSIS_PROMPT
from app.agents.prompts.answer_analysis_resume import LLM_JUDGE_PROMPT
from app.agents.structured_output import parse_json_response
from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


async def analyze_single_answer_node(state: InterviewState) -> Dict[str, Any]:
    """Analyze the current answer based on its source type.

    Always uses single-shot LLM evaluation — the fastest and most reliable path.
    Multi-agent orchestration is used for resume analysis, question generation,
    and report generation but NOT for answer evaluation.
    """
    settings = get_settings()

    answers = state.get("answers", [])
    questions = state.get("questions", [])
    question_index = state.get("question_index", 0)

    if question_index >= len(answers):
        logger.warning(f"No answer found for question index {question_index}")
        return {}

    return await _single_agent_analysis(state, settings)


async def _single_agent_analysis(
    state: InterviewState, settings
) -> Dict[str, Any]:
    """Single-shot LLM evaluation — fast, reliable, no tool-calling overhead."""
    answers = state.get("answers", [])
    questions = state.get("questions", [])
    question_index = state.get("question_index", 0)

    current_answer = answers[question_index]
    current_question = questions[question_index] if question_index < len(questions) else {}
    source_type = current_question.get("source_type", "resume_experience")

    if source_type == "knowledge_base":
        analysis = await _analyze_kb_answer(state, current_question, current_answer, settings)
    else:
        analysis = await _analyze_resume_answer(state, current_question, current_answer, settings)

    analysis["answer_id"] = current_answer.get("question_id", "")
    analysis["question_id"] = current_question.get("question_id", "")
    analysis["eval_mode"] = "rag_hybrid" if source_type == "knowledge_base" else "llm_judge"

    return {
        "answer_analyses": [analysis],
        "current_phase": "answer_analysis",
    }


# ---- Single-agent helper functions (unchanged from original) ----

async def _analyze_kb_answer(
    state: InterviewState,
    question: Dict[str, Any],
    answer: Dict[str, Any],
    settings,
) -> Dict[str, Any]:
    llm = create_deepseek_llm(settings, temperature=0.2, max_tokens=2048)
    question_text = question.get("question_text", "")
    transcript = answer.get("transcript_text", "")
    standard_answer = question.get("ai_reference_answer", "")
    retrieved_chunks = []

    prompt = KB_ANSWER_ANALYSIS_PROMPT.format(
        question_text=question_text,
        standard_answer=standard_answer if standard_answer else "标准答案暂未提供",
        candidate_answer=transcript,
        retrieved_chunks=json.dumps(retrieved_chunks, ensure_ascii=False),
    )

    start_time = time.time()
    response = await llm.ainvoke(prompt)
    elapsed_ms = int((time.time() - start_time) * 1000)
    content = response.content if hasattr(response, "content") else str(response)
    analysis = parse_json_response(content)
    analysis["tokens_used"] = (
        getattr(response, "usage_metadata", {}).get("total_tokens", 0)
        if hasattr(response, "usage_metadata") else 0
    )
    analysis["processing_ms"] = elapsed_ms
    analysis["retrieved_chunks"] = retrieved_chunks
    return analysis


async def _analyze_resume_answer(
    state: InterviewState,
    question: Dict[str, Any],
    answer: Dict[str, Any],
    settings,
) -> Dict[str, Any]:
    llm = create_deepseek_llm(settings, temperature=0.2, max_tokens=2048)
    resume_ocr = state.get("resume_ocr", {})
    resume_context = question.get("source_resume_context", "")
    question_text = question.get("question_text", "")
    ai_reference = question.get("ai_reference_answer", "")
    transcript = answer.get("transcript_text", "")

    prompt = LLM_JUDGE_PROMPT.format(
        resume_context=resume_context or json.dumps(
            resume_ocr.get("parsed", {}), ensure_ascii=False
        )[:2000],
        question_text=question_text,
        ai_reference_answer=ai_reference or "无参考答案",
        candidate_answer=transcript,
    )

    start_time = time.time()
    response = await llm.ainvoke(prompt)
    elapsed_ms = int((time.time() - start_time) * 1000)
    content = response.content if hasattr(response, "content") else str(response)
    analysis = parse_json_response(content)

    accuracy = analysis.pop("accuracy", {})
    completeness = analysis.pop("completeness", {})
    clarity = analysis.pop("clarity", {})
    technical_depth = analysis.pop("technical_depth", {})

    analysis["accuracy_score"] = accuracy.get("score", accuracy) if isinstance(accuracy, dict) else (accuracy if isinstance(accuracy, int) else 0)
    analysis["accuracy_reasoning"] = accuracy.get("reasoning", "") if isinstance(accuracy, dict) else ""
    analysis["completeness_score"] = completeness.get("score", completeness) if isinstance(completeness, dict) else (completeness if isinstance(completeness, int) else 0)
    analysis["completeness_reasoning"] = completeness.get("reasoning", "") if isinstance(completeness, dict) else ""
    analysis["clarity_score"] = clarity.get("score", clarity) if isinstance(clarity, dict) else (clarity if isinstance(clarity, int) else 0)
    analysis["clarity_reasoning"] = clarity.get("reasoning", "") if isinstance(clarity, dict) else ""
    analysis["technical_depth_score"] = technical_depth.get("score", technical_depth) if isinstance(technical_depth, dict) else (technical_depth if isinstance(technical_depth, int) else 0)
    analysis["technical_depth_reasoning"] = technical_depth.get("reasoning", "") if isinstance(technical_depth, dict) else ""

    analysis["tokens_used"] = (
        getattr(response, "usage_metadata", {}).get("total_tokens", 0)
        if hasattr(response, "usage_metadata") else 0
    )
    analysis["processing_ms"] = elapsed_ms
    return analysis
