"""Agentic RAG retriever with LLM-powered decision loop.

Implements the 7-step agentic retrieval pattern:
  1. DECIDE:      Should I retrieve for this query?
  2. FORMULATE:   Generate optimal search query
  3. EXECUTE:     Multi-strategy search (dense + sparse)
  4. EVALUATE:    LLM judges relevance of retrieved documents
  5. RE-RETRIEVE: If relevance < threshold, reformulate and retry
  6. SYNTHESIZE:  Summarize why results are relevant
  7. CITE:        Reference which KB items were used

Unlike the existing HybridRetriever which blindly searches, this class
wraps retrieval with agentic decision-making: it decides whether retrieval
is warranted, formulates optimal queries, evaluates result quality, and
re-formulates queries when results are poor.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.language_models import BaseChatModel

from app.rag.hybrid_retriever import HybridRetriever
from app.rag.reranker import Reranker
from app.agents.prompts.agentic_rag import (
    QUERY_FORMULATION_PROMPT,
    RELEVANCE_JUDGMENT_PROMPT,
    RESULT_SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """A single retrieved document with metadata and relevance scores."""

    id: str
    content: str  # Full KB item content (question + answer)
    similarity: float = 0.0  # Vector cosine similarity
    relevance_score: float = 0.0  # LLM-judged relevance (0-1)
    category_id: str = ""
    difficulty: str = "medium"
    tags: List[str] = field(default_factory=list)


@dataclass
class RetrievalResult:
    """Complete result of an agentic retrieval operation."""

    documents: List[RetrievedDocument]
    original_query: str
    reformulated_queries: List[str] = field(default_factory=list)
    attempts: int = 0
    strategy: str = "dense"  # dense, sparse, hybrid, skipped, fallback
    citations: List[str] = field(default_factory=list)
    relevance_summary: str = ""
    overall_relevance: float = 0.0
    retrieval_ms: int = 0


class AgenticRetriever:
    """Agentic RAG: LLM-powered retrieval with decision, formulation, evaluation.

    Wraps HybridRetriever + Reranker with LLM-based relevance judgment
    and query reformulation. Agents use this instead of calling the
    HybridRetriever directly, gaining autonomous control over when and
    how to retrieve knowledge.

    Usage:
        agentic_rag = AgenticRetriever(
            hybrid_retriever=hybrid_retriever,
            reranker=reranker,
            llm=llm,
        )

        result = await agentic_rag.retrieve(
            context="Evaluating a candidate's answer about Python async/await",
            query="How does Python's asyncio event loop work?",
        )
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        reranker: Reranker,
        llm: BaseChatModel,
        max_retry_attempts: int = 1,
        relevance_threshold: float = 0.65,
        top_k: int = 5,
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.llm = llm
        self.max_retry_attempts = max_retry_attempts
        self.relevance_threshold = relevance_threshold
        self.top_k = top_k

    async def retrieve(
        self,
        context: str,
        query: str,
        category_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        force_retrieve: bool = False,
    ) -> RetrievalResult:
        """Execute the full 7-step agentic retrieval loop.

        Args:
            context: Full context of WHY we are searching (helps LLM decide/formulate).
            query: The initial search query (may be reformulated by the agent).
            category_id: Optional KB category filter.
            difficulty: Optional difficulty filter.
            force_retrieve: If True, skip the "decide" step and always search.

        Returns:
            RetrievalResult with documents, relevance scores, citations, and metadata.
        """
        start_time = time.time()

        result = RetrievalResult(
            documents=[],
            original_query=query,
        )

        # ---- Step 1-2: Decide and formulate ----
        if not force_retrieve:
            should_retrieve, search_query = await self._decide_and_formulate(
                context, query
            )
            if not should_retrieve:
                result.strategy = "skipped"
                result.retrieval_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"AgenticRAG: Skipped retrieval for query '{query[:60]}...' — "
                    f"agent decided external knowledge is not needed"
                )
                return result
        else:
            search_query = query

        result.reformulated_queries.append(search_query)

        # ---- Step 3-5: Multi-attempt retrieval with reformulation ----
        avg_relevance = 0.0
        for attempt in range(self.max_retry_attempts + 1):
            result.attempts = attempt + 1

            # Step 3: Execute dense search via HybridRetriever
            raw_results = await self.hybrid_retriever.retrieve(
                query_text=search_query,
                top_k=self.top_k * 2,  # Get more candidates for reranking
                category_id=category_id,
                difficulty=difficulty,
            )

            # Rerank results
            ranked = await self.reranker.rerank(
                search_query, raw_results, top_k=self.top_k
            )

            # Build RetrievedDocument list
            docs = [
                RetrievedDocument(
                    id=r.get("id", ""),
                    content=r.get("content", ""),
                    similarity=r.get("similarity", 0.0),
                    category_id=r.get("category_id", ""),
                    difficulty=r.get("difficulty", "medium"),
                    tags=r.get("tags", []),
                )
                for r in ranked
            ]
            result.documents = docs

            # Step 4: Evaluate relevance with LLM
            avg_relevance = await self._evaluate_relevance(query, docs)

            # Step 5: Re-retrieve if quality is low
            if (
                avg_relevance >= self.relevance_threshold
                or attempt >= self.max_retry_attempts
            ):
                # Good enough or no more retries
                for doc in docs:
                    doc.relevance_score = avg_relevance
                break

            # Reformulate query for next attempt
            new_query = await self._reformulate_query(
                context, query, docs, avg_relevance
            )
            if new_query != search_query:
                search_query = new_query
                result.reformulated_queries.append(search_query)
            else:
                # Query unchanged — no point retrying
                break

        result.overall_relevance = avg_relevance

        # ---- Step 6-7: Synthesize and cite ----
        result.citations = [
            f"KB:{doc.id}"
            for doc in result.documents
            if doc.relevance_score >= self.relevance_threshold
        ]
        result.relevance_summary = await self._synthesize_relevance(
            query, result.documents
        )
        result.retrieval_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"AgenticRAG: query='{query[:50]}...', "
            f"strategy={result.strategy}, attempts={result.attempts}, "
            f"docs={len(result.documents)}, avg_rel={avg_relevance:.2f}, "
            f"citations={len(result.citations)}, time={result.retrieval_ms}ms"
        )
        return result

    # ---- Private methods implementing each step ----

    async def _decide_and_formulate(
        self, context: str, query: str
    ) -> tuple:
        """Step 1-2: Decide whether to retrieve and formulate optimal query.

        Returns:
            Tuple of (should_retrieve: bool, search_query: str).
        """
        prompt = QUERY_FORMULATION_PROMPT.format(
            context=context,
            original_query=query,
        )
        try:
            response = await self.llm.ainvoke(prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            result = json.loads(content)
            should = result.get("should_retrieve", True)
            search_query = result.get("search_query", query)
            reasoning = result.get("reasoning", "")
            logger.debug(
                f"AgenticRAG decide: should_retrieve={should}, "
                f"query='{search_query}', reasoning='{reasoning[:80]}'"
            )
            return should, search_query
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"AgenticRAG decision parsing failed: {e}, "
                f"defaulting to retrieve with original query"
            )
            return True, query

    async def _evaluate_relevance(
        self, original_query: str, documents: List[RetrievedDocument]
    ) -> float:
        """Step 4: LLM judges relevance of retrieved documents.

        Returns average relevance score 0.0–1.0.
        """
        if not documents:
            return 0.0

        doc_texts = "\n---\n".join(
            f"[Doc {d.id}]: {d.content[:500]}" for d in documents
        )
        prompt = RELEVANCE_JUDGMENT_PROMPT.format(
            query=original_query,
            documents=doc_texts,
        )
        try:
            response = await self.llm.ainvoke(prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            parsed = json.loads(content)
            scores = parsed.get("scores", [])
            if scores and isinstance(scores, list) and all(isinstance(s, (int, float)) for s in scores):
                avg = sum(scores) / len(scores)
                logger.debug(f"AgenticRAG LLM relevance: scores={scores}, avg={avg:.3f}")
                return avg
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"AgenticRAG relevance evaluation failed: {e}")

        # Fallback: use average cosine similarity as relevance proxy
        sims = [d.similarity for d in documents if d.similarity > 0]
        return sum(sims) / len(sims) if sims else 0.5

    async def _reformulate_query(
        self,
        context: str,
        original_query: str,
        docs: List[RetrievedDocument],
        avg_relevance: float,
    ) -> str:
        """Step 5: Reformulate search query when relevance is low."""
        doc_summary = ", ".join(
            f"{d.id}(sim={d.similarity:.2f})" for d in docs[:3]
        )
        reformulation_context = (
            f"{context}\n"
            f"Previous query: '{original_query}'\n"
            f"Retrieved documents (avg relevance={avg_relevance:.2f}): {doc_summary}\n"
            f"NOTE: Previous query returned low-quality results. "
            f"Reformulate with different keywords, broader/narrower scope, "
            f"or alternative technical terms."
        )
        prompt = QUERY_FORMULATION_PROMPT.format(
            context=reformulation_context,
            original_query=original_query,
        )
        try:
            response = await self.llm.ainvoke(prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            result = json.loads(content)
            new_query = result.get("search_query", original_query)
            logger.info(
                f"AgenticRAG reformulated query: "
                f"'{original_query[:40]}...' → '{new_query[:40]}...'"
            )
            return new_query
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"AgenticRAG query reformulation failed: {e}")
            return original_query

    async def _synthesize_relevance(
        self, query: str, documents: List[RetrievedDocument]
    ) -> str:
        """Step 6-7: Generate a brief summary of why retrieved docs are relevant."""
        if not documents:
            return "No relevant documents found."

        relevant_docs = [
            d
            for d in documents
            if d.relevance_score >= self.relevance_threshold
        ]
        if not relevant_docs:
            return (
                f"No documents met relevance threshold "
                f"({self.relevance_threshold})."
            )

        doc_texts = "\n---\n".join(
            f"[{d.id}]: {d.content[:300]}" for d in relevant_docs
        )
        prompt = RESULT_SYNTHESIS_PROMPT.format(
            query=query,
            documents=doc_texts,
        )
        try:
            response = await self.llm.ainvoke(prompt)
            return (
                response.content
                if hasattr(response, "content")
                else str(response)
            )
        except Exception as e:
            logger.warning(f"AgenticRAG synthesis failed: {e}")
            return f"Retrieved {len(relevant_docs)} potentially relevant documents."
