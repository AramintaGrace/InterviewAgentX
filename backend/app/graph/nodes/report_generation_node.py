"""Interview Report Generation graph node."""

import json
import logging
import time
from typing import Any, Dict

from app.agents.agent_factory import create_deepseek_reasoner
from app.agents.prompts.report_generation import REPORT_GENERATION_PROMPT
from app.agents.structured_output import parse_json_response
from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


async def generate_report_node(state: InterviewState) -> Dict[str, Any]:
    """Generate the final interview report from all answer analysis summaries.

    Key design: This node reads structured answer_analyses summaries,
    NOT raw transcripts, avoiding token overflow.
    """
    settings = get_settings()
    llm = create_deepseek_reasoner(settings, temperature=0.2)

    # Build compact summaries from structured data
    resume_ocr = state.get("resume_ocr", {})
    resume_analyses = state.get("resume_analyses", [])
    answer_analyses = state.get("answer_analyses", [])
    questions = state.get("questions", [])

    # Candidate info from parsed OCR
    parsed = resume_ocr.get("parsed", {}) if resume_ocr else {}
    candidate_info = json.dumps({
        "name": parsed.get("name", "未知"),
        "current_role": parsed.get("current_role", ""),
        "skills": parsed.get("skills", []),
    }, ensure_ascii=False)

    # Resume analysis summary (compact)
    last_analysis = resume_analyses[-1] if resume_analyses else {}
    resume_summary = json.dumps({
        "overall_assessment": last_analysis.get("overall_assessment", ""),
        "strengths": last_analysis.get("strengths", []),
        "weaknesses": last_analysis.get("weaknesses", []),
        "experience_relevance_score": last_analysis.get("experience_relevance_score", 0),
    }, ensure_ascii=False)

    # Build question review summaries from structured analyses
    question_reviews = []
    for i, analysis in enumerate(answer_analyses):
        q = questions[i] if i < len(questions) else {}
        question_reviews.append({
            "question_text": q.get("question_text", ""),
            "source_type": q.get("source_type", ""),
            "eval_mode": analysis.get("eval_mode", ""),
            "overall_score": analysis.get("overall_score", 0),
            "strengths": analysis.get("strengths", []),
            "areas_for_improvement": analysis.get("areas_for_improvement", []),
            "assessment": analysis.get("assessment", ""),
        })

    answer_summaries = json.dumps(question_reviews, ensure_ascii=False)

    prompt = REPORT_GENERATION_PROMPT.format(
        candidate_info=candidate_info,
        resume_analysis_summary=resume_summary,
        answer_analyses=answer_summaries[:6000],
    )

    start_time = time.time()
    try:
        response = await llm.ainvoke(prompt)
        elapsed_ms = int((time.time() - start_time) * 1000)
        content = response.content if hasattr(response, "content") else str(response)

        report = parse_json_response(content)
        report["session_id"] = state.get("session_id", "")
        report["tokens_used"] = getattr(response, "usage_metadata", {}).get("total_tokens", 0) if hasattr(response, "usage_metadata") else 0
        report["processing_ms"] = elapsed_ms

        logger.info(f"Interview report generated in {elapsed_ms}ms")

        return {
            "interview_report": report,
            "current_phase": "completed",
        }
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return {
            "errors": [{"phase": "report_generation", "error_message": str(e)}],
            "current_phase": "completed",
        }
