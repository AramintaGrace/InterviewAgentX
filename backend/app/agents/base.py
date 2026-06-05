"""Agent base class with tool-calling loop and structured output handling.

Each multi-agent follows this execution pattern:
  1. Receive state dict from the graph node
  2. Build system message + user message (with tool definitions if applicable)
  3. Invoke LLM via LangChain with tool binding
  4. Handle tool calls in a loop (up to max_iterations):
     a. LLM decides whether to call a tool or produce final output
     b. If tool calls: execute tools, append results to messages, loop
     c. If no tool calls: parse final output and return
  5. Return state update dict (merged into LangGraph state)

Unlike the current pipeline where each node just calls llm.ainvoke(prompt),
multi-agent nodes use a decision loop: LLM → tool calls → integrate → decide...
This gives each agent autonomous control over its actions.

Design decisions:
  - Uses LangChain's native tool binding (bind_tools) — no subgraph needed
  - Each agent is stateless; state is passed via the execute() method
  - Tools are injected at construction time via closure
  - max_iterations prevents infinite tool-calling loops
  - All agents produce structured JSON output (parsed by parse_output)
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.agents.structured_output import parse_json_response

logger = logging.getLogger(__name__)


class AgentTrace:
    """Captures an agent's reasoning and tool-call decisions for audit/debug."""

    def __init__(self, agent_name: str = ""):
        self.agent_name = agent_name
        self.decisions: List[str] = []
        self.tool_calls_made: List[str] = []
        self.iterations: int = 0
        self.tokens_used: int = 0
        self.processing_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "decisions": self.decisions,
            "tool_calls_made": self.tool_calls_made,
            "iterations": self.iterations,
            "tokens_used": self.tokens_used,
            "processing_ms": self.processing_ms,
        }


class BaseAgent(ABC):
    """Abstract base for all multi-agent implementations.

    Subclasses define:
      - system_prompt: The agent's role and behavior specification
      - tools: Optional list of LangChain BaseTool instances
      - max_iterations: Maximum tool-calling loop iterations (default 5)

    The execute() method runs the full agent loop:
      SystemMessage(prompt) + HumanMessage(state) → LLM
        → [ToolCall → ToolResult → LLM] × N
        → FinalOutput → parse_output → state_update_dict
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Optional[List[BaseTool]] = None,
        max_iterations: int = 5,
        name: str = "",
    ):
        self.llm = llm
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.name = name or self.__class__.__name__
        self._bound_llm: Optional[BaseChatModel] = None

    # ---- Subclass interface ----

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's system prompt string defining its role and behavior."""
        ...

    def build_user_message(self, state: Dict[str, Any]) -> str:
        """Build the user message from current state.

        Override in subclasses for custom message construction.
        Default: serializes state as JSON.
        """
        import json

        # Include only relevant top-level keys to avoid token overflow
        safe_keys = {
            "session_id", "candidate_id", "resume_id",
            "current_phase", "question_source", "question_index",
            "total_questions",
        }
        compact_state = {k: v for k, v in state.items() if k in safe_keys and v is not None}
        return json.dumps(compact_state, ensure_ascii=False, default=str)

    @abstractmethod
    def parse_output(self, content: str) -> Dict[str, Any]:
        """Parse the final LLM output into a state update dict.

        This is called after the tool-calling loop ends (either the LLM
        produces a final response without tool calls, or max_iterations
        is reached). The returned dict is merged into LangGraph state.
        """
        ...

    # ---- Tool management ----

    @property
    def bound_llm(self) -> BaseChatModel:
        """LLM instance with tools bound (lazy initialization).

        When tools are available, the LLM is bound with tool definitions
        so it can decide to call tools during the agent loop.
        """
        if self._bound_llm is None and self.tools:
            self._bound_llm = self.llm.bind_tools(self.tools)
        return self._bound_llm or self.llm

    def _get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Find a tool by name in the agent's tool list."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    # ---- Main execution loop ----

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full agent loop.

        Flow:
          SystemMessage + HumanMessage
          → LLM decides (text response OR tool calls)
          → If tool calls: execute tools, append results, loop
          → If no tool calls: parse final text into state update

        Args:
            state: Current InterviewState dict.

        Returns:
            Dict to merge into LangGraph state (e.g. {"resume_analyses": [...]}).
        """
        trace = AgentTrace(agent_name=self.name)
        start_time = time.time()

        # Build initial messages
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self.build_user_message(state)),
        ]

        final_content = ""
        for iteration in range(self.max_iterations):
            trace.iterations = iteration + 1
            logger.debug(f"[{self.name}] Iteration {iteration + 1}/{self.max_iterations}")

            # Invoke LLM (with tools if available)
            llm_to_use = self.bound_llm if self.tools else self.llm
            response = await llm_to_use.ainvoke(messages)

            # Accumulate token usage
            try:
                meta = getattr(response, "usage_metadata", {}) or {}
                trace.tokens_used += meta.get("total_tokens", 0)
            except Exception:
                pass

            # Check for tool calls
            tool_calls = getattr(response, "tool_calls", []) or []
            if not tool_calls:
                # No tool calls → this is the final response
                final_content = (
                    response.content
                    if hasattr(response, "content")
                    else str(response)
                )
                trace.processing_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[{self.name}] Completed: {trace.iterations} iterations, "
                    f"{len(trace.tool_calls_made)} tool calls, "
                    f"{trace.tokens_used} tokens, {trace.processing_ms}ms"
                )
                result = self.parse_output(final_content)
                result.setdefault("_agent_trace", trace.to_dict())
                return result

            # Process tool calls
            messages.append(response)
            for tc in tool_calls:
                tool_name = tc.get("name", "unknown")
                tool_args = tc.get("args", {})
                tc_id = tc.get("id", "")

                trace.tool_calls_made.append(tool_name)
                decision = f"Calling {tool_name}({json.dumps(tool_args, ensure_ascii=False, default=str)[:100]})"
                trace.decisions.append(decision)
                logger.debug(f"[{self.name}] {decision}")

                tool_result = await self._execute_tool(
                    tool_name, tool_args, state
                )
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tc_id)
                )

        # Max iterations reached — do one final call to force JSON output
        logger.warning(
            f"[{self.name}] Reached max_iterations ({self.max_iterations}) "
            f"with {len(trace.tool_calls_made)} tool calls. Forcing final response."
        )
        try:
            final_response = await self.llm.ainvoke(messages)  # no tools, force text
            final_content = (
                final_response.content
                if hasattr(final_response, "content")
                else str(final_response)
            )
        except Exception:
            final_content = "{}"

        trace.processing_ms = int((time.time() - start_time) * 1000)
        result = self.parse_output(final_content)
        result.setdefault("_agent_trace", trace.to_dict())
        return result

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Execute a single tool call by name.

        Args:
            tool_name: Name of the tool to execute.
            tool_args: Arguments to pass to the tool.
            state: Current InterviewState (passed for context).

        Returns:
            Tool execution result as a string.
        """
        tool = self._get_tool_by_name(tool_name)
        if tool is None:
            logger.error(f"[{self.name}] Unknown tool: {tool_name}")
            return f"Error: Unknown tool '{tool_name}'"

        try:
            result = await tool.ainvoke(tool_args)
            return str(result)
        except Exception as e:
            logger.error(
                f"[{self.name}] Tool '{tool_name}' failed: {e}",
                exc_info=True,
            )
            return f"Error executing {tool_name}: {str(e)}"
