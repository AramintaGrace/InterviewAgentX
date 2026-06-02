"""Hybrid retriever combining dense vectors + optional BM25 sparse vectors."""

import logging
from typing import List, Optional

from app.services.embedding_service import EmbeddingService
from app.services.milvus_service import MilvusService

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining dense embedding search with Milvus.

    For knowledge base questions, this retriever:
    1. Embeds the candidate's answer
    2. Searches Milvus for the most similar standard answers
    3. Returns retrieved chunks with similarity scores
    """

    def __init__(
        self,
        milvus_service: MilvusService,
        embedding_service: EmbeddingService,
    ):
        self.milvus = milvus_service
        self.embeddings = embedding_service

    async def retrieve(
        self,
        query_text: str,
        top_k: int = 5,
        category_id: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[dict]:
        """Retrieve the most relevant knowledge base answers.

        Args:
            query_text: The candidate's answer text to compare against.
            top_k: Number of results to return.
            category_id: Optional category filter.
            difficulty: Optional difficulty filter.

        Returns:
            List of retrieved chunks with similarity scores and metadata.
        """
        # Generate embedding for the candidate's answer
        query_vector = await self.embeddings.embed_text(query_text)

        # Search Milvus
        results = await self.milvus.search(
            query_vector=query_vector,
            top_k=top_k,
            category_id=category_id,
            difficulty=difficulty,
        )

        logger.debug(f"Hybrid retriever found {len(results)} results")
        return results
