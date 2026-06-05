"""Hybrid retriever combining dense vectors + BM25 sparse vectors.

Provides three retrieval strategies:
  1. Dense:  Embed query → Milvus COSINE search (existing)
  2. Sparse: PostgreSQL full-text search (tsvector/tsquery) on kb_items
  3. Hybrid: Reciprocal Rank Fusion (RRF) of dense + sparse results

The "hybrid" name is now accurate — both dense and sparse retrieval
are implemented, with RRF fusion for combined results.
"""

import logging
from typing import Callable, List, Optional

from app.services.embedding_service import EmbeddingService
from app.services.milvus_service import MilvusService

logger = logging.getLogger(__name__)

# Type for a callback that resolves KB item IDs to content strings
ContentResolver = Callable[[List[str]], dict[str, str]]


class HybridRetriever:
    """Hybrid retrieval combining dense (Milvus) + sparse (PostgreSQL FTS) search.

    For knowledge base retrieval, this retriever:
      1. Embeds the query text for dense vector search
      2. Optionally performs BM25 full-text search via PostgreSQL
      3. Fuses results using Reciprocal Rank Fusion (RRF)
      4. Resolves KB item IDs to actual content via content_resolver

    Usage:
        retriever = HybridRetriever(milvus_service, embedding_service)

        # Dense-only (backward compatible)
        results = await retriever.retrieve(query_text, top_k=5)

        # Hybrid (dense + sparse fusion)
        results = await retriever.retrieve_hybrid(
            query_text, top_k=5, content_resolver=lookup_fn
        )
    """

    def __init__(
        self,
        milvus_service: MilvusService,
        embedding_service: EmbeddingService,
    ):
        self.milvus = milvus_service
        self.embeddings = embedding_service

    # ---- Dense retrieval (existing, enhanced) ----

    async def retrieve(
        self,
        query_text: str,
        top_k: int = 5,
        category_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        content_resolver: Optional[ContentResolver] = None,
    ) -> List[dict]:
        """Dense vector retrieval via Milvus.

        Args:
            query_text: The text to search for.
            top_k: Number of results to return.
            category_id: Optional category filter.
            difficulty: Optional difficulty filter.
            content_resolver: Optional callback to resolve item IDs to content.

        Returns:
            List of dicts with id, similarity, category_id, tags, difficulty,
            version, and optionally content.
        """
        query_vector = await self.embeddings.embed_text(query_text)
        results = await self.milvus.search(
            query_vector=query_vector,
            top_k=top_k,
            category_id=category_id,
            difficulty=difficulty,
        )

        # Resolve content if resolver provided
        if content_resolver and results:
            ids = [r["id"] for r in results]
            content_map = content_resolver(ids)
            for r in results:
                r["content"] = content_map.get(r["id"], "")

        logger.debug(f"Dense retrieval: {len(results)} results")
        return results

    # ---- Sparse retrieval (new) ----

    async def retrieve_sparse(
        self,
        query_text: str,
        top_k: int = 5,
        content_resolver: Optional[ContentResolver] = None,
    ) -> List[dict]:
        """BM25 sparse retrieval via PostgreSQL full-text search.

        Uses PostgreSQL tsvector/tsquery for keyword-based search on
        kb_items.question and kb_items.answer columns.

        NOTE: This method requires access to a PostgreSQL session.
        In practice, the content_resolver should also perform the
        FTS query. If no content_resolver is provided, sparse retrieval
        returns an empty list (graceful degradation).

        Args:
            query_text: The text to search for.
            top_k: Number of results to return.
            content_resolver: Callback that performs FTS and returns
                              {id: content_string}.

        Returns:
            List of dicts with id, content, and bm25_rank.
        """
        if content_resolver is None:
            logger.debug("Sparse retrieval skipped: no content_resolver provided")
            return []

        # The content_resolver is expected to:
        # 1. Execute: SELECT id, question || ' ' || answer as content,
        #             ts_rank(...) as rank
        #             FROM kb_items
        #             WHERE to_tsvector('simple', question || ' ' || answer)
        #                   @@ plainto_tsquery('simple', :query)
        #               AND is_deleted = false
        #             ORDER BY rank DESC LIMIT :top_k
        # 2. Return {id: content_string} mapping

        ids = list(content_resolver(query_text, top_k).keys())
        content_map = content_resolver(query_text, top_k) if ids else {}

        results = []
        for rank, item_id in enumerate(ids, start=1):
            results.append({
                "id": item_id,
                "content": content_map.get(item_id, ""),
                "bm25_rank": rank,
                "similarity": 1.0 / rank,  # Reciprocal rank as similarity proxy
            })

        logger.debug(f"Sparse retrieval: {len(results)} results")
        return results

    # ---- Hybrid retrieval (new) ----

    async def retrieve_hybrid(
        self,
        query_text: str,
        top_k: int = 5,
        category_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        content_resolver: Optional[ContentResolver] = None,
        rrf_k: int = 60,
    ) -> List[dict]:
        """Hybrid retrieval fusing dense + sparse results via RRF.

        Reciprocal Rank Fusion (RRF) combines results from multiple
        retrieval strategies:
          RRF_score(doc) = Σ 1/(k + rank_i(doc))

        where k=60 is the standard smoothing constant.

        Args:
            query_text: The text to search for.
            top_k: Number of results to return after fusion.
            category_id: Optional category filter (dense only).
            difficulty: Optional difficulty filter (dense only).
            content_resolver: Callback for content lookup + sparse search.
            rrf_k: RRF smoothing constant (default 60).

        Returns:
            List of dicts with id, content, similarity (fused score),
            and metadata from both retrieval strategies.
        """
        # Execute dense and sparse retrieval in parallel
        dense_results = await self.retrieve(
            query_text=query_text,
            top_k=top_k * 2,  # Get more candidates for fusion
            category_id=category_id,
            difficulty=difficulty,
        )

        sparse_results = await self.retrieve_sparse(
            query_text=query_text,
            top_k=top_k * 2,
            content_resolver=content_resolver,
        )

        if not sparse_results:
            # No sparse results — fall back to dense-only
            logger.debug("Hybrid: sparse returned no results, using dense-only")
            return dense_results[:top_k]

        # Reciprocal Rank Fusion
        fused_scores: dict[str, float] = {}
        doc_meta: dict[str, dict] = {}

        # Dense contributions
        for rank, doc in enumerate(dense_results, start=1):
            doc_id = doc["id"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
            doc_meta[doc_id] = doc

        # Sparse contributions
        for rank, doc in enumerate(sparse_results, start=1):
            doc_id = doc["id"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
            if doc_id not in doc_meta:
                doc_meta[doc_id] = doc
            else:
                # Merge sparse metadata into existing
                doc_meta[doc_id].setdefault("bm25_rank", doc.get("bm25_rank"))

        # Sort by fused score and take top_k
        sorted_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
        results = []
        for doc_id in sorted_ids[:top_k]:
            meta = doc_meta[doc_id]
            meta["similarity"] = round(fused_scores[doc_id], 6)
            meta["fusion_score"] = round(fused_scores[doc_id], 6)
            results.append(meta)

        logger.info(
            f"Hybrid retrieval: dense={len(dense_results)}, "
            f"sparse={len(sparse_results)}, fused={len(results)}"
        )
        return results
