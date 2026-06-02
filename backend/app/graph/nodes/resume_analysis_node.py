"""Resume Analysis graph node."""

import logging
import time
from typing import Any, Dict

from app.agents.agent_factory import create_deepseek_llm
from app.agents.prompts.resume_analysis import RESUME_ANALYSIS_PROMPT
from app.agents.structured_output import parse_json_response
from app.config import get_settings
from app.graph.state import InterviewState

logger = logging.getLogger(__name__)


async def resume_analysis_node(state: InterviewState) -> Dict[str, Any]:
    """Analyze the candidate's resume using the Resume Analysis Agent.

    Reads OCR text from state, invokes DeepSeek LLM, and returns
    structured analysis as a ResumeAnalysisOutput appended to state.
    """
    settings = get_settings()
    llm = create_deepseek_llm(settings, temperature=0.3)

    resume_ocr = state.get("resume_ocr")
    if not resume_ocr:
        logger.warning("No resume OCR data in state, skipping analysis")
        return {
            "resume_analyses": [],
            "current_phase": "question_generation",
        }

    resume_text = resume_ocr.get("raw_text", "")
    parsed = resume_ocr.get("parsed", {})

    # Compact representation: limit text to avoid token overflow
    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:6000] + ("..." if len(resume_text) > 6000 else ""),
    )

    start_time = time.time()
    try:
        response = await llm.ainvoke(prompt)
        elapsed_ms = int((time.time() - start_time) * 1000)
        content = response.content if hasattr(response, "content") else str(response)

        analysis = parse_json_response(content)
        analysis["resume_id"] = resume_ocr.get("resume_id", "")
        analysis["tokens_used"] = getattr(response, "usage_metadata", {}).get("total_tokens", 0) if hasattr(response, "usage_metadata") else 0
        analysis["processing_ms"] = elapsed_ms

        logger.info(f"Resume analysis completed in {elapsed_ms}ms")

        return {
            "resume_analyses": [analysis],
            "current_phase": "question_generation",
        }
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        return {
            "errors": [{"phase": "resume_analysis", "error_message": str(e)}],
            "current_phase": "question_generation",
        }
