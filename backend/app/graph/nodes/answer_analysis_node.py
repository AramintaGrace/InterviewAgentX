"""Answer Analysis graph node — handles both RAG hybrid and LLM-as-a-Judge modes."""

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

    Routes to:
    - RAG hybrid evaluation for knowledge_base questions
    - LLM-as-a-Judge evaluation for resume questions
    """
    settings = get_settings()

    answers = state.get("answers", [])
    questions = state.get("questions", [])
    question_index = state.get("question_index", 0)

    if question_index >= len(answers):
        logger.warning(f"No answer found for question index {question_index}")
        return {}

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


async def _analyze_kb_answer(
    state: InterviewState,
    question: Dict[str, Any],
    answer: Dict[str, Any],
    settings,
) -> Dict[str, Any]:
    """RAG hybrid evaluation: retrieve standard answer from Milvus, compare with candidate answer."""
    llm = create_deepseek_llm(settings, temperature=0.2)

    question_text = question.get("question_text", "")
    transcript = answer.get("transcript_text", "")
    kb_item_id = question.get("source_kb_item_id", "")

    # In a real implementation, we'd retrieve from Milvus using the kb_item_id
    # For now, use the AI reference answer if available
    standard_answer = question.get("ai_reference_answer", "")
    retrieved_chunks = []  # Would be populated from Milvus search

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
    analysis["tokens_used"] = getattr(response, "usage_metadata", {}).get("total_tokens", 0) if hasattr(response, "usage_metadata") else 0
    analysis["processing_ms"] = elapsed_ms
    analysis["retrieved_chunks"] = retrieved_chunks

    return analysis


async def _analyze_resume_answer(
    state: InterviewState,
    question: Dict[str, Any],
    answer: Dict[str, Any],
    settings,
) -> Dict[str, Any]:
    """LLM-as-a-Judge evaluation for resume-based questions."""
    llm = create_deepseek_llm(settings, temperature=0.2)

    resume_ocr = state.get("resume_ocr", {})
    resume_context = question.get("source_resume_context", "")
    question_text = question.get("question_text", "")
    ai_reference = question.get("ai_reference_answer", "")
    transcript = answer.get("transcript_text", "")

    prompt = LLM_JUDGE_PROMPT.format(
        resume_context=resume_context or json.dumps(resume_ocr.get("parsed", {}), ensure_ascii=False)[:2000],
        question_text=question_text,
        ai_reference_answer=ai_reference or "无参考答案",
        candidate_answer=transcript,
    )

    start_time = time.time()
    response = await llm.ainvoke(prompt)
    elapsed_ms = int((time.time() - start_time) * 1000)

    content = response.content if hasattr(response, "content") else str(response)
    analysis = parse_json_response(content)

    # Flatten dimension scores into top-level fields
    accuracy = analysis.pop("accuracy", {})
    completeness = analysis.pop("completeness", {})
    clarity = analysis.pop("clarity", {})
    technical_depth = analysis.pop("technical_depth", {})

    analysis["accuracy_score"] = accuracy.get("score", 0)
    analysis["accuracy_reasoning"] = accuracy.get("reasoning", "")
    analysis["completeness_score"] = completeness.get("score", 0)
    analysis["completeness_reasoning"] = completeness.get("reasoning", "")
    analysis["clarity_score"] = clarity.get("score", 0)
    analysis["clarity_reasoning"] = clarity.get("reasoning", "")
    analysis["technical_depth_score"] = technical_depth.get("score", 0)
    analysis["technical_depth_reasoning"] = technical_depth.get("reasoning", "")

    analysis["tokens_used"] = getattr(response, "usage_metadata", {}).get("total_tokens", 0) if hasattr(response, "usage_metadata") else 0
    analysis["processing_ms"] = elapsed_ms

    return analysis
