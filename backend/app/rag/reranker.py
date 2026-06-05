"""LLM-based cross-encoder reranker for improving retrieval precision.

Replaces the placeholder cosine-sort implementation with an actual
LLM-powered reranker that scores (query, document) pairs for relevance.

The LLM is used as a cross-encoder: it reads the query and each document
together, then assigns a relevance score. This is more accurate than
cosine similarity alone because the LLM understands semantic relationships
that vector similarity might miss.

Usage:
    reranker = Reranker(llm=llm)
    ranked = await reranker.rerank(query, documents, top_k=3)
"""

import json
import logging
from typing import List, Optional

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


class Reranker:
    """LLM-based cross-encoder reranker for search results.

    Scores each (query, document) pair using an LLM, then returns
    the top_k documents sorted by LLM-assigned relevance.

    Falls back gracefully to cosine similarity sorting when:
      - No LLM is provided
      - LLM call fails
      - Only one document to rank
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        """Initialize the reranker.

        Args:
            llm: Optional LLM for cross-encoder scoring. If None,
                 falls back to cosine similarity sort.
        """
        self.llm = llm

    async def rerank(
        self,
        query: str,
        documents: List[dict],
        top_k: int = 3,
    ) -> List[dict]:
        """Re-rank retrieved documents by LLM cross-encoder relevance.

        Args:
            query: The original query text.
            documents: List of retrieved documents. Each must have at least
                       'id' and either 'content' or other text fields.
                       Optional: 'similarity' for fallback scoring.
            top_k: Number of top results to return after reranking.

        Returns:
            Re-ranked list of documents with 'rerank_score' added.
        """
        if not documents:
            return []

        if len(documents) <= 1:
            for d in documents:
                d["rerank_score"] = d.get("similarity", 0.5)
            return documents

        # If no LLM available, fall back to cosine similarity sort
        if self.llm is None:
            logger.debug("Reranker: no LLM, using cosine similarity fallback")
            return self._cosine_fallback(documents, top_k)

        try:
            ranked = await self._llm_rerank(query, documents, top_k)
            return ranked
        except Exception as e:
            logger.warning(
                f"LLM reranking failed ({e}), falling back to cosine similarity"
            )
            return self._cosine_fallback(documents, top_k)

    async def _llm_rerank(
        self,
        query: str,
        documents: List[dict],
        top_k: int,
    ) -> List[dict]:
        """Use LLM as cross-encoder to score each document against the query.

        The LLM evaluates each document's relevance to the query and
        assigns a score from 0.0 (irrelevant) to 1.0 (highly relevant).
        """
        # Build document summaries for LLM evaluation
        doc_summaries = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            if not content:
                # Try to construct content from available fields
                parts = []
                for field in ["question", "answer", "title", "text"]:
                    if field in doc:
                        parts.append(str(doc[field])[:300])
                content = " | ".join(parts) if parts else f"Document {doc.get('id', i)}"

            doc_summaries.append({
                "index": i,
                "id": doc.get("id", str(i)),
                "content": content[:600],  # Truncate per doc
            })

        # Format for LLM
        docs_text = "\n---\n".join(
            f"[Doc {d['index']}] ID={d['id']}: {d['content']}"
            for d in doc_summaries
        )

        prompt = f"""你是一个搜索结果相关性评估助手。请评估以下文档与查询的相关性。

## 查询
{query[:500]}

## 待评估文档
{docs_text}

## 任务
对每个文档，评估其与查询的相关性，分数 0.0（完全无关）到 1.0（高度相关）。

请严格返回JSON：
{{"scores": [{{"index": 0, "score": 0.95, "reason": "..."}}, ...], "top_{top_k}_indices": [0, 2, 1]}}
"""

        response = await self.llm.ainvoke(prompt)
        content = (
            response.content if hasattr(response, "content") else str(response)
        )

        try:
            parsed = json.loads(content)
            scores = parsed.get("scores", [])

            # Build score map
            score_map: dict[int, float] = {}
            for s in scores:
                idx = s.get("index", -1)
                sc = s.get("score", 0.5)
                if 0 <= idx < len(documents):
                    score_map[idx] = sc

            # Assign rerank scores (default 0.5 for unscored docs)
            for i, doc in enumerate(documents):
                doc["rerank_score"] = score_map.get(i, 0.5)

            # Sort by rerank score
            ranked = sorted(
                documents,
                key=lambda d: d.get("rerank_score", 0),
                reverse=True,
            )
            result = ranked[:top_k]

            logger.debug(
                f"LLM reranker: {len(documents)} docs → "
                f"top {len(result)}, "
                f"scores={[round(d.get('rerank_score', 0), 3) for d in result[:5]]}"
            )
            return result

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse LLM reranker response: {e}")
            raise

    def _cosine_fallback(
        self,
        documents: List[dict],
        top_k: int,
    ) -> List[dict]:
        """Fallback: sort by existing similarity score (cosine distance)."""
        for doc in documents:
            doc["rerank_score"] = doc.get("similarity", 0.5)

        sorted_docs = sorted(
            documents,
            key=lambda d: d.get("similarity", 0),
            reverse=True,
        )
        return sorted_docs[:top_k]
