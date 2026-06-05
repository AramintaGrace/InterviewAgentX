"""Agent factory for creating DeepSeek-powered LangChain agents.

Provides factory functions for:
  1. Base LLM instances (ChatOpenAI configured for DeepSeek API)
  2. Tool-binding LLM instances for multi-agent use
  3. Complete agent constructors with pre-configured tools

Multi-agent mode (multi_agent_enabled=True) uses tool-calling agents
with autonomous decision loops. Single-agent mode (default) uses the
traditional prompt-template pipeline for backward compatibility.
"""

import logging
from typing import List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.config import Settings

logger = logging.getLogger(__name__)


# ============================================================================
# Base LLM Factory Functions
# ============================================================================


def create_deepseek_llm(
    settings: Settings,
    temperature: float = 0.3,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance configured for DeepSeek API.

    DeepSeek API is OpenAI-compatible, so we use ChatOpenAI with
    DeepSeek's base URL and API key.
    """
    return ChatOpenAI(
        model=model or settings.deepseek_model_chat,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_deepseek_reasoner(
    settings: Settings,
    temperature: float = 0.1,
    max_tokens: int = 8192,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance for DeepSeek reasoner model.

    Used for complex analysis tasks (report generation, detailed evaluation).
    """
    return ChatOpenAI(
        model=settings.deepseek_model_reasoner,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ============================================================================
# Tool-Binding Constructors (Multi-Agent Mode)
# ============================================================================


def create_llm_with_tools(
    settings: Settings,
    tools: List[BaseTool],
    temperature: float = 0.2,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Create an LLM instance with tools bound for agent use.

    The returned LLM has tool definitions attached so it can
    autonomously decide to call tools during the agent loop.

    Args:
        settings: Application settings.
        tools: List of LangChain BaseTool instances to bind.
        temperature: LLM temperature for agent decision-making.
        model: Optional model override.
        max_tokens: Maximum response tokens.

    Returns:
        ChatOpenAI instance with tool binding.
    """
    llm = ChatOpenAI(
        model=model or settings.deepseek_model_chat,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return llm.bind_tools(tools)


def create_agentic_llm(
    settings: Settings,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> ChatOpenAI:
    """Create a lightweight LLM for AgenticRAG decisions.

    This LLM is used for quick decisions in the agentic RAG loop
    (query formulation, relevance judgment) where full max_tokens
    is not needed. Uses lower temperature for consistent judgments.

    Args:
        settings: Application settings.
        temperature: Low temperature for consistent decisions.
        max_tokens: Small token limit for quick responses.

    Returns:
        ChatOpenAI instance optimized for agentic RAG decisions.
    """
    return ChatOpenAI(
        model=settings.deepseek_model_chat,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
