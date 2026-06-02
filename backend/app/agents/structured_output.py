"""Structured output parser utilities for agent responses."""

import json
import logging
import re
from typing import Any, Dict, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def parse_json_response(response_content: str) -> Dict[str, Any]:
    """Parse JSON from an LLM response, handling markdown code blocks.

    Args:
        response_content: Raw LLM response text.

    Returns:
        Parsed JSON dictionary.
    """
    content = response_content.strip()

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

    # Try to find JSON object boundaries
    if not content.startswith("{"):
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end + 1]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from response: {content[:200]}...")
        # Return a safe fallback
        return {"error": "Failed to parse agent output", "raw": content[:500]}


def parse_structured_output(
    response_content: str,
    schema: Type[BaseModel],
) -> BaseModel:
    """Parse LLM response into a Pydantic model.

    Args:
        response_content: Raw LLM response text.
        schema: Target Pydantic model class.

    Returns:
        Validated Pydantic model instance.
    """
    data = parse_json_response(response_content)
    return schema.model_validate(data)
