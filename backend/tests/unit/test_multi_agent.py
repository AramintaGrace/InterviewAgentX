"""Unit tests for multi-agent architecture and agentic RAG components.

Tests cover:
  - BaseAgent tool-calling loop
  - AgenticRetriever 7-step retrieval flow
  - Agent factory functions
  - Tool creation and injection
  - State backward compatibility

Run: pytest backend/tests/unit/test_multi_agent.py -v
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# BaseAgent Tests
# ============================================================================


class TestBaseAgent:
    """Test the BaseAgent abstract class and tool-calling loop."""

    @pytest.mark.asyncio
    async def test_agent_execute_no_tools(self):
        """Agent without tools should call LLM once and parse output."""
        from app.agents.base import BaseAgent
        from langchain_core.language_models import BaseChatModel

        # Create a concrete test agent
        mock_llm = AsyncMock(spec=BaseChatModel)
        mock_response = MagicMock()
        mock_response.content = '{"result": "success", "score": 85}'
        mock_response.tool_calls = []
        mock_llm.ainvoke.return_value = mock_response

        class TestAgent(BaseAgent):
            @property
            def system_prompt(self) -> str:
                return "You are a test agent."

            def parse_output(self, content: str) -> dict:
                return json.loads(content)

        agent = TestAgent(llm=mock_llm, tools=[], max_iterations=3, name="TestAgent")
        result = await agent.execute({"key": "value"})

        assert result["result"] == "success"
        assert result["score"] == 85
        assert "_agent_trace" in result  # trace is always included
        mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_execute_with_tools(self, monkeypatch):
        """Agent with tools should handle tool calls in a loop."""
        from app.agents.base import BaseAgent
        from langchain_core.language_models import BaseChatModel
        from langchain_core.tools import tool

        @tool
        async def get_data(query: str) -> str:
            """Get data for a query."""
            return f"Data for {query}"

        # First call: tool call, second call: final response
        call_count = 0
        mock_response_1 = MagicMock()
        mock_response_1.content = ""
        mock_response_1.tool_calls = [
            {"name": "get_data", "args": {"query": "test"}, "id": "call_1"}
        ]
        mock_response_2 = MagicMock()
        mock_response_2.content = '{"result": "done"}'
        mock_response_2.tool_calls = []

        async def mock_ainvoke(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_1
            return mock_response_2

        # Create a mock LLM that properly awaits
        mock_llm = MagicMock()
        mock_llm.ainvoke = mock_ainvoke

        # Patch the bound_llm property to return ainvoke mock
        class ToolAgent(BaseAgent):
            @property
            def system_prompt(self) -> str:
                return "You have tools."

            def parse_output(self, content: str) -> dict:
                return json.loads(content)

            @property
            def bound_llm(self):
                return mock_llm

        agent = ToolAgent(
            llm=MagicMock(), tools=[get_data], max_iterations=5, name="ToolAgent"
        )
        result = await agent.execute({})

        assert result["result"] == "done"
        assert "_agent_trace" in result

    @pytest.mark.asyncio
    async def test_agent_max_iterations(self):
        """Agent should stop after max_iterations even with tool calls."""
        from app.agents.base import BaseAgent
        from langchain_core.language_models import BaseChatModel
        from langchain_core.tools import tool

        @tool
        async def endless_tool(x: str) -> str:
            """Process data endlessly (never reaches final output)."""
            return f"Processed {x}"

        # Always return tool calls (never final)
        call_count = 0
        mock_response = MagicMock()
        mock_response.content = ""
        mock_response.tool_calls = [
            {"name": "endless_tool", "args": {"x": "data"}, "id": "call_1"}
        ]

        async def mock_ainvoke(messages):
            nonlocal call_count
            call_count += 1
            return mock_response

        mock_llm = MagicMock()
        mock_llm.ainvoke = mock_ainvoke

        class InfiniteAgent(BaseAgent):
            @property
            def system_prompt(self) -> str:
                return "Infinite loop agent."

            def parse_output(self, content: str) -> dict:
                return {"status": "max_iterations_reached"}

            @property
            def bound_llm(self):
                return mock_llm

        agent = InfiniteAgent(
            llm=MagicMock(), tools=[endless_tool], max_iterations=2, name="InfiniteAgent"
        )
        result = await agent.execute({})

        assert result["status"] == "max_iterations_reached"
        assert "_agent_trace" in result

    @pytest.mark.asyncio
    async def test_trace_included(self):
        """Agent trace should be included in result."""
        from app.agents.base import BaseAgent
        from langchain_core.language_models import BaseChatModel

        mock_llm = AsyncMock(spec=BaseChatModel)
        mock_response = MagicMock()
        mock_response.content = '{"ok": true}'
        mock_response.tool_calls = []
        mock_response.usage_metadata = {"total_tokens": 100}
        mock_llm.ainvoke.return_value = mock_response

        class TraceAgent(BaseAgent):
            @property
            def system_prompt(self) -> str:
                return "Trace test."

            def parse_output(self, content: str) -> dict:
                return json.loads(content)

        agent = TraceAgent(llm=mock_llm, name="TraceAgent")
        result = await agent.execute({})

        trace = result.get("_agent_trace")
        assert trace is not None
        assert trace["agent"] == "TraceAgent"
        assert trace["iterations"] == 1
        assert trace["tokens_used"] == 100
        assert "processing_ms" in trace


# ============================================================================
# AgenticRetriever Tests
# ============================================================================


class TestAgenticRetriever:
    """Test the 7-step agentic RAG retrieval loop."""

    @pytest.mark.asyncio
    async def test_retrieve_skips_when_not_needed(self):
        """Agent decides retrieval is not needed — should skip search."""
        from app.rag.agentic_retriever import AgenticRetriever

        mock_hybrid = AsyncMock()
        mock_reranker = AsyncMock()
        mock_llm = AsyncMock()

        # LLM decides no retrieval needed
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "should_retrieve": False,
            "search_query": "",
            "reasoning": "Already have enough context",
        })
        mock_llm.ainvoke.return_value = mock_response

        retriever = AgenticRetriever(
            hybrid_retriever=mock_hybrid,
            reranker=mock_reranker,
            llm=mock_llm,
        )

        result = await retriever.retrieve(
            context="Testing retrieval skip",
            query="test query",
            force_retrieve=False,
        )

        assert result.strategy == "skipped"
        assert result.documents == []
        assert result.attempts == 0
        mock_hybrid.retrieve.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_retrieve_bypasses_decision(self):
        """force_retrieve=True should skip the decision step."""
        from app.rag.agentic_retriever import AgenticRetriever

        mock_hybrid = AsyncMock()
        mock_hybrid.retrieve.return_value = [
            {"id": "doc1", "similarity": 0.9, "content": "test content"}
        ]

        mock_reranker = AsyncMock()
        mock_reranker.rerank.return_value = [
            {"id": "doc1", "similarity": 0.9, "content": "test content"}
        ]

        mock_llm = AsyncMock()
        # LLM for relevance evaluation
        mock_eval_response = MagicMock()
        mock_eval_response.content = json.dumps({
            "scores": [0.85],
            "overall_relevance": 0.85,
            "explanation": "Highly relevant",
        })
        # LLM for synthesis
        mock_synth_response = MagicMock()
        mock_synth_response.content = "Document is relevant."
        mock_llm.ainvoke.side_effect = [mock_eval_response, mock_synth_response]

        retriever = AgenticRetriever(
            hybrid_retriever=mock_hybrid,
            reranker=mock_reranker,
            llm=mock_llm,
            relevance_threshold=0.65,
        )

        result = await retriever.retrieve(
            context="Testing force retrieve",
            query="test query",
            force_retrieve=True,
        )

        assert result.strategy == "dense"  # dense is set before loop
        assert len(result.documents) == 1
        assert result.documents[0].id == "doc1"
        mock_hybrid.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_citations_generated(self):
        """Citations should be generated for relevant documents."""
        from app.rag.agentic_retriever import AgenticRetriever

        mock_hybrid = AsyncMock()
        mock_hybrid.retrieve.return_value = [
            {"id": "kb-123", "similarity": 0.88, "content": "Rich content here"}
        ]

        mock_reranker = AsyncMock()
        mock_reranker.rerank.return_value = [
            {"id": "kb-123", "similarity": 0.88, "content": "Rich content here"}
        ]

        mock_llm = AsyncMock()
        mock_eval = MagicMock()
        mock_eval.content = json.dumps({"scores": [0.9], "overall_relevance": 0.9})
        mock_synth = MagicMock()
        mock_synth.content = "Relevant."
        mock_llm.ainvoke.side_effect = [mock_eval, mock_synth]

        retriever = AgenticRetriever(
            hybrid_retriever=mock_hybrid,
            reranker=mock_reranker,
            llm=mock_llm,
            relevance_threshold=0.65,
        )

        result = await retriever.retrieve(
            context="Test",
            query="test",
            force_retrieve=True,
        )

        assert "KB:kb-123" in result.citations

    @pytest.mark.asyncio
    async def test_relevance_fallback_to_similarity(self):
        """When LLM relevance fails, fallback to cosine similarity average."""
        from app.rag.agentic_retriever import AgenticRetriever

        mock_hybrid = AsyncMock()
        mock_hybrid.retrieve.return_value = [
            {"id": "d1", "similarity": 0.7, "content": "c1"},
            {"id": "d2", "similarity": 0.5, "content": "c2"},
        ]

        mock_reranker = AsyncMock()
        mock_reranker.rerank.return_value = [
            {"id": "d1", "similarity": 0.7, "content": "c1"},
            {"id": "d2", "similarity": 0.5, "content": "c2"},
        ]

        mock_llm = AsyncMock()
        # Return invalid JSON for relevance eval → triggers fallback
        mock_llm.ainvoke.side_effect = [
            MagicMock(content="not json"),   # evaluation fails
            MagicMock(content="Relevant enough."),  # synthesis
        ]

        retriever = AgenticRetriever(
            hybrid_retriever=mock_hybrid,
            reranker=mock_reranker,
            llm=mock_llm,
        )

        result = await retriever.retrieve(
            context="Test", query="test", force_retrieve=True
        )

        # Fallback: avg of 0.7 and 0.5 = 0.6
        assert result.overall_relevance == 0.6


# ============================================================================
# Tools Tests
# ============================================================================


class TestTools:
    """Test tool creation and injection."""

    @pytest.mark.asyncio
    async def test_create_orchestrator_tools(self):
        """Orchestrator tools should be created and callable."""
        from app.agents.tools import create_orchestrator_tools

        state = {
            "session_id": "test-123",
            "current_phase": "answering",
            "question_source": "resume",
            "question_index": 2,
            "total_questions": 5,
            "questions": [{"q": "q1"}, {"q": "q2"}, {"q": "q3"}],
            "answers": [{"a": "a1"}, {"a": "a2"}],
            "answer_analyses": [{"score": 80}],
            "resume_ocr": {"raw_text": "test"},
            "resume_analyses": [{"score": 75}],
            "errors": [],
            "interview_difficulty": "medium",
        }

        tools = create_orchestrator_tools(state_provider=lambda: state)
        assert len(tools) == 3

        # Test get_state_summary
        summary_tool = tools[0]
        result = await summary_tool.ainvoke({})
        data = json.loads(result)
        assert data["session_id"] == "test-123"
        assert data["current_phase"] == "answering"
        assert data["total_questions"] == 5
        assert data["answers_submitted"] == 2

    @pytest.mark.asyncio
    async def test_create_resume_analyst_tools(self):
        """Resume analyst tools should provide resume text."""
        from app.agents.tools import create_resume_analyst_tools

        state = {
            "resume_ocr": {
                "raw_text": "John Doe\nPython Developer",
                "parsed": {"name": "John Doe", "skills": ["Python"]},
                "file_name": "resume.pdf",
            },
            "candidate_id": "cand-1",
        }

        tools = create_resume_analyst_tools(state_provider=lambda: state)
        assert len(tools) == 3

        # Test get_full_resume_text
        text_tool = tools[0]
        result = await text_tool.ainvoke({})
        data = json.loads(result)
        assert "John Doe" in data["raw_text"]
        assert data["parsed"]["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_create_report_synthesizer_tools(self):
        """Report synthesizer tools should collect analyses."""
        from app.agents.tools import create_report_synthesizer_tools

        state = {
            "questions": [
                {"question_text": "Q1", "source_type": "resume_experience"},
                {"question_text": "Q2", "source_type": "knowledge_base"},
            ],
            "answer_analyses": [
                {
                    "overall_score": 85,
                    "eval_mode": "llm_judge",
                    "strengths": ["clear"],
                    "areas_for_improvement": ["detail"],
                    "assessment": "Good",
                },
                {
                    "overall_score": 70,
                    "eval_mode": "rag_hybrid",
                    "strengths": ["accurate"],
                    "areas_for_improvement": ["depth"],
                    "assessment": "Adequate",
                },
            ],
            "resume_analyses": [{"experience_relevance_score": 80}],
        }

        tools = create_report_synthesizer_tools(state_provider=lambda: state)
        assert len(tools) == 2

        # Test collect_all_analyses
        collect_tool = tools[0]
        result = await collect_tool.ainvoke({})
        data = json.loads(result)
        assert data["total_questions"] == 2
        assert data["analyzed_count"] == 2
        assert len(data["question_reviews"]) == 2

        # Test compute_dimension_scores
        compute_tool = tools[1]
        result = await compute_tool.ainvoke({})
        data = json.loads(result)
        assert "dimension_scores" in data
        assert "overall_avg" in data["dimension_scores"]


# ============================================================================
# Agent Factory Tests
# ============================================================================


class TestAgentFactory:
    """Test agent factory functions."""

    def test_create_deepseek_llm(self):
        """Should create a ChatOpenAI instance with DeepSeek config."""
        from app.agents.agent_factory import create_deepseek_llm
        from app.config import Settings

        settings = Settings(
            deepseek_api_key="test-key",
            deepseek_base_url="https://test.api.com/v1",
            deepseek_model_chat="test-model",
        )

        llm = create_deepseek_llm(settings, temperature=0.5, max_tokens=1024)
        assert llm is not None
        assert llm.model_name == "test-model"

    def test_create_deepseek_reasoner(self):
        """Should create a reasoner-configured ChatOpenAI."""
        from app.agents.agent_factory import create_deepseek_reasoner
        from app.config import Settings

        settings = Settings(
            deepseek_api_key="test-key",
            deepseek_base_url="https://test.api.com/v1",
            deepseek_model_reasoner="test-reasoner",
        )

        llm = create_deepseek_reasoner(settings)
        assert llm is not None
        assert llm.model_name == "test-reasoner"

    def test_create_agentic_llm(self):
        """Should create a lightweight LLM for agentic RAG decisions."""
        from app.agents.agent_factory import create_agentic_llm
        from app.config import Settings

        settings = Settings(
            deepseek_api_key="test-key",
            deepseek_base_url="https://test.api.com/v1",
            deepseek_model_chat="test-chat",
        )

        llm = create_agentic_llm(settings)
        assert llm is not None
        assert llm.model_name == "test-chat"


# ============================================================================
# State Backward Compatibility Tests
# ============================================================================


class TestStateBackwardCompatibility:
    """Ensure InterviewState changes don't break existing checkpoints."""

    def test_old_state_compatible(self):
        """Old state dict (without multi-agent fields) should be compatible."""
        # Simulate a state from an old checkpoint
        old_state = {
            "session_id": "s1",
            "thread_id": "t1",
            "candidate_id": "c1",
            "resume_id": "r1",
            "current_phase": "answering",
            "question_source": "resume",
            "question_index": 2,
            "total_questions": 5,
            "resume_ocr": None,
            "resume_analyses": [],
            "questions": [],
            "answers": [],
            "answer_analyses": [],
            "interview_report": None,
            "errors": [],
            "started_at": "2025-01-01",
            "completed_at": None,
            # No multi-agent fields
        }

        # Accessing old fields should work
        assert old_state["session_id"] == "s1"
        assert old_state["current_phase"] == "answering"

        # New fields should be gracefully absent
        assert old_state.get("orchestrator_decision") is None
        assert old_state.get("agent_traces") is None
        assert old_state.get("interview_difficulty") is None

    def test_new_state_with_defaults(self):
        """New state with multi-agent fields should support both old and new access."""
        from app.graph.state import InterviewState

        # Verify the TypedDict defines new fields
        # This is a compile-time check — the actual validation happens in LangGraph
        new_state = {
            "session_id": "s1",
            "thread_id": "t1",
            "candidate_id": "c1",
            "resume_id": "r1",
            "current_phase": "init",
            "question_source": "resume",
            "question_index": 0,
            "total_questions": 0,
            "resume_ocr": None,
            "resume_analyses": [],
            "questions": [],
            "answers": [],
            "answer_analyses": [],
            "interview_report": None,
            "errors": [],
            "started_at": "2025-01-01",
            "completed_at": None,
            "orchestrator_decision": None,
            "agent_traces": [],
            "pending_follow_ups": [],
            "interview_difficulty": "medium",
            "kb_retrieval_cache": None,
            "resilience_context": None,
            "kb_configs": None,
            "pool_ids": None,
        }
        assert new_state["interview_difficulty"] == "medium"
        assert new_state["session_id"] == "s1"


# ============================================================================
# HybridRetriever Tests
# ============================================================================


class TestHybridRetriever:
    """Test the enhanced HybridRetriever with dense and sparse retrieval."""

    @pytest.mark.asyncio
    async def test_dense_retrieval(self):
        """Dense retrieval should embed query and search Milvus."""
        from app.rag.hybrid_retriever import HybridRetriever

        mock_milvus = AsyncMock()
        mock_milvus.search.return_value = [
            {"id": "d1", "similarity": 0.9, "category_id": "cat1"}
        ]

        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text.return_value = [0.1, 0.2, 0.3]

        retriever = HybridRetriever(mock_milvus, mock_embeddings)
        results = await retriever.retrieve("test query", top_k=3)

        assert len(results) == 1
        assert results[0]["id"] == "d1"
        mock_embeddings.embed_text.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_hybrid_retrieval_without_sparse(self):
        """Hybrid retrieval without sparse results should return dense-only."""
        from app.rag.hybrid_retriever import HybridRetriever

        mock_milvus = AsyncMock()
        mock_milvus.search.return_value = [
            {"id": "d1", "similarity": 0.85, "category_id": "cat1"},
            {"id": "d2", "similarity": 0.75, "category_id": "cat2"},
        ]

        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text.return_value = [0.1, 0.2, 0.3]

        retriever = HybridRetriever(mock_milvus, mock_embeddings)
        results = await retriever.retrieve_hybrid("test", top_k=3)

        # Without content_resolver, sparse returns empty, so hybrid = dense
        assert len(results) == 2


# ============================================================================
# Reranker Tests
# ============================================================================


class TestReranker:
    """Test the LLM-based reranker."""

    @pytest.mark.asyncio
    async def test_cosine_fallback_without_llm(self):
        """Without LLM, reranker should sort by cosine similarity."""
        from app.rag.reranker import Reranker

        reranker = Reranker(llm=None)  # No LLM → fallback
        docs = [
            {"id": "d1", "similarity": 0.5},
            {"id": "d2", "similarity": 0.9},
            {"id": "d3", "similarity": 0.7},
        ]

        ranked = await reranker.rerank("query", docs, top_k=2)
        assert len(ranked) == 2
        assert ranked[0]["id"] == "d2"  # Highest similarity first
        assert ranked[1]["id"] == "d3"

    @pytest.mark.asyncio
    async def test_single_document_passthrough(self):
        """Single document should be returned as-is."""
        from app.rag.reranker import Reranker

        reranker = Reranker()
        docs = [{"id": "only", "similarity": 0.8}]
        ranked = await reranker.rerank("query", docs)
        assert len(ranked) == 1
        assert ranked[0]["id"] == "only"
