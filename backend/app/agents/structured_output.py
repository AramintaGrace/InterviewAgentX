"""Structured output parser utilities for agent responses."""

import json
import logging
import re
from typing import Any, Dict, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def parse_json_response(response_content: str) -> Dict[str, Any]:
    """Parse JSON from an LLM response, handling markdown code blocks and truncation.

    Handles:
      - Markdown code fences (```json ... ```)
      - Text before/after JSON
      - Truncated JSON arrays (recovers partial items)
      - Truncated JSON objects (best-effort recovery)

    Args:
        response_content: Raw LLM response text.

    Returns:
        Parsed JSON (dict or list). On failure, returns dict with "error" key.
    """
    content = response_content.strip()

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

    # Try to find JSON boundaries (object or array)
    starts_with_brace = content.startswith("{") or content.startswith("[")
    if not starts_with_brace:
        obj_start = content.find("{")
        arr_start = content.find("[")
        if arr_start != -1 and (arr_start < obj_start or obj_start == -1):
            start, end_char = arr_start, "]"
        else:
            start, end_char = obj_start, "}"
        if start != -1:
            end = content.rfind(end_char)
            if end != -1:
                content = content[start:end + 1]

    # Attempt 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.debug(f"JSON parse failed at pos {e.pos}: {e.msg}")

    # Attempt 2: Try to recover truncated JSON array
    if content.strip().startswith("["):
        recovered = _recover_truncated_array(content)
        if recovered is not None:
            logger.warning(
                f"Recovered {len(recovered)} items from truncated JSON array "
                f"(last item may be incomplete)"
            )
            return recovered

    # Attempt 3: Try to close incomplete JSON object
    if content.strip().startswith("{"):
        recovered = _recover_truncated_object(content)
        if recovered is not None:
            logger.warning("Recovered partial JSON object (some fields may be missing)")
            return recovered

    logger.warning(f"All JSON parse attempts failed for: {content[:200]}...")
    return {"error": "Failed to parse agent output", "raw": content[:500]}


def _recover_truncated_array(text: str) -> list | None:
    """Try to recover items from a truncated JSON array.

    Strategy: find all complete objects in the array by matching {} pairs.
    Works when LLM output hits max_tokens mid-generation.
    """
    text = text.strip()
    if not text.startswith("["):
        return None

    items = []
    i = 1  # skip opening [
    depth = 0
    item_start = None
    in_string = False
    escape = False

    while i < len(text):
        ch = text[i]

        if escape:
            escape = False
            i += 1
            continue

        if ch == '\\':
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            i += 1
            continue

        if in_string:
            i += 1
            continue

        if ch == '{':
            if depth == 0:
                item_start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and item_start is not None:
                try:
                    obj = json.loads(text[item_start:i + 1])
                    items.append(obj)
                except json.JSONDecodeError:
                    pass  # skip malformed item
                item_start = None
        elif ch == ']' and depth == 0:
            # Properly closed array
            try:
                return json.loads(text[:i + 1])
            except json.JSONDecodeError:
                break

        i += 1

    # If we found at least one complete object, return the partial list
    if items:
        return items

    return None


def _recover_truncated_object(text: str) -> dict | None:
    """Try to recover a truncated JSON object by appending closing braces."""
    text = text.strip()
    if not text.startswith("{"):
        return None

    # Count unclosed braces and brackets
    brace_depth = 0
    bracket_depth = 0
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
        elif ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1

    # Close open strings and containers
    suffix = ""
    if in_string:
        suffix += '"'
        in_string = False
    suffix += "]" * bracket_depth + "}" * brace_depth

    if not suffix:
        return None  # nothing to close

    try:
        return json.loads(text + suffix)
    except json.JSONDecodeError:
        # Last resort: try removing the trailing incomplete key-value pair
        # Find last complete comma
        last_comma = text.rfind(',"')
        if last_comma > 0:
            truncated = text[:last_comma] + "}"  + "]" * bracket_depth + "}" * (brace_depth - 1)
            if not truncated.startswith("{"):
                truncated = "{" + truncated[1:]
            try:
                return json.loads(truncated)
            except json.JSONDecodeError:
                pass

    return None


def parse_structured_output(
    response_content: str,
    schema: Type[BaseModel],
) -> BaseModel:
    """Parse LLM response into a Pydantic model."""
    data = parse_json_response(response_content)
    return schema.model_validate(data)
