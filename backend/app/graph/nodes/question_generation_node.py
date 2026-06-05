"""Question Generation graph node — delegates to QuestionCuratorAgent in multi-agent mode."""

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

    Multi-agent mode: delegates to QuestionCuratorAgent with AgenticRAG tools.
    Single-agent mode: original llm.ainvoke(prompt) pipeline.

    Supports three modes:
    - resume: Generate from resume experiences and projects
    - knowledge_base: Select from knowledge base items
    - mixed: Mix of both sources
    """
    settings = get_settings()
    question_source = state.get("question_source", "resume")
    total_questions = state.get("total_questions", 5)

    if settings.multi_agent_enabled:
        return await _multi_agent_generation(state, settings)
    else:
        return await _single_agent_generation(state, settings)


async def _multi_agent_generation(
    state: InterviewState, settings
) -> Dict[str, Any]:
    """Multi-agent: delegate to QuestionCuratorAgent with AgenticRAG."""
    from app.agents.question_curator import QuestionCuratorAgent
    from app.agents.tools import create_question_curator_tools
    from app.rag.agentic_retriever import AgenticRetriever
    from app.rag.hybrid_retriever import HybridRetriever
    from app.rag.reranker import Reranker
    from app.agents.agent_factory import create_agentic_llm
    from app.services.embedding_service import EmbeddingService
    from app.services.milvus_service import MilvusService

    try:
        # Build agentic RAG components
        milvus_svc = MilvusService(settings)
        embedding_svc = EmbeddingService(settings)
        hybrid_retriever = HybridRetriever(milvus_svc, embedding_svc)

        rag_llm = create_agentic_llm(settings)
        reranker = Reranker(llm=rag_llm)

        agentic_retriever = AgenticRetriever(
            hybrid_retriever=hybrid_retriever,
            reranker=reranker,
            llm=rag_llm,
            max_retry_attempts=settings.agentic_rag_max_retries,
            relevance_threshold=settings.agentic_rag_relevance_threshold,
            top_k=settings.agentic_rag_top_k,
        )

        # Create agent
        llm = create_deepseek_llm(settings, temperature=0.5, max_tokens=8192)
        tools = create_question_curator_tools(
            agentic_retriever=agentic_retriever,
            state_provider=lambda: state,
        )
        agent = QuestionCuratorAgent(
            llm=llm,
            tools=tools,
            max_iterations=settings.agent_max_iterations,
        )

        result = await agent.execute(state)

        # Assign IDs and order
        questions = result.get("questions", [])
        for i, q in enumerate(questions):
            q["question_id"] = str(uuid.uuid4())
            q["question_order"] = i + 1

        # Merge agent trace
        trace = result.pop("_agent_trace", None)
        if trace:
            result.setdefault("agent_traces", [])
            result["agent_traces"].append(trace)

        result.setdefault("question_index", 0)
        result.setdefault("current_phase", "answering")
        logger.info(f"QuestionCurator generated {len(questions)} questions via multi-agent mode")
        return result

    except Exception as e:
        logger.error(f"QuestionCuratorAgent failed: {e}", exc_info=True)
        return await _single_agent_generation(state, settings)


async def _single_agent_generation(
    state: InterviewState, settings
) -> Dict[str, Any]:
    """Original single-agent pipeline for question generation."""
    llm = create_deepseek_llm(settings, temperature=0.5, max_tokens=8192)
    question_source = state.get("question_source", "resume")
    total_questions = state.get("total_questions", 5)

    try:
        if question_source == "resume":
            questions = await _generate_from_resume(state, llm, total_questions)
        elif question_source == "knowledge_base":
            questions = await _generate_from_kb(state, llm, total_questions)
        else:
            questions = await _generate_mixed(state, llm, total_questions)

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


# ---- Single-agent helper functions (unchanged from original) ----

async def _generate_from_resume(
    state: InterviewState, llm, count: int
) -> list[Dict[str, Any]]:
    resume_ocr = state.get("resume_ocr", {})
    resume_analyses = state.get("resume_analyses", [])
    resume_context = json.dumps(resume_ocr.get("parsed", {}), ensure_ascii=False)
    analysis_text = json.dumps(
        resume_analyses[-1] if resume_analyses else {}, ensure_ascii=False
    )
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
    resume_ocr = state.get("resume_ocr", {})
    resume_analyses = state.get("resume_analyses", [])
    resume_context = json.dumps(resume_ocr.get("parsed", {}), ensure_ascii=False)
    analysis_text = json.dumps(
        resume_analyses[-1] if resume_analyses else {}, ensure_ascii=False
    )
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
