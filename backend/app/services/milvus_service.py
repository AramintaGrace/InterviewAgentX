"""Milvus vector database service."""

import logging
import time
from typing import List, Optional

from pymilvus import (
    Collection,
    connections,
    utility,
)

from app.config import Settings
from app.utils.exceptions import MilvusException

logger = logging.getLogger(__name__)


class MilvusService:
    """Service for Milvus vector database operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.host = settings.milvus_host
        self.port = settings.milvus_port
        self.collection_name = settings.milvus_collection
        self._collection: Optional[Collection] = None
        self._connected = False

    def connect(self) -> None:
        """Connect to Milvus server."""
        if self._connected:
            return
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
            )
            self._connected = True
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise MilvusException(f"Milvus connection failed: {e}")

    @property
    def collection(self) -> Collection:
        """Get or load the collection."""
        self.connect()
        if self._collection is None:
            if not utility.has_collection(self.collection_name):
                raise MilvusException(f"Collection '{self.collection_name}' not found")
            self._collection = Collection(name=self.collection_name)
            self._collection.load()
        return self._collection

    async def insert_vector(
        self,
        entity_id: str,
        answer_vector: List[float],
        category_id: str = "",
        tags: Optional[List[str]] = None,
        difficulty: str = "medium",
        question_sparse_vector: Optional[dict] = None,
    ) -> None:
        """Insert a vector entity into Milvus."""
        try:
            data = [{
                "id": entity_id,
                "answer_vector": answer_vector,
                "question_sparse_vector": question_sparse_vector or {},
                "category_id": category_id,
                "tags": tags or [],
                "difficulty": difficulty,
                "version": 1,
                "is_deleted": False,
                "created_at": int(time.time() * 1000),
            }]

            self.collection.insert(data)
            logger.info(f"Inserted vector for entity {entity_id}")
        except Exception as e:
            logger.error(f"Failed to insert vector: {e}")
            raise MilvusException(f"Vector insertion failed: {e}")

    async def update_vector(
        self,
        entity_id: str,
        answer_vector: List[float],
        category_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> None:
        """Update an existing vector (delete old + insert new)."""
        await self.delete_vector(entity_id)
        await self.insert_vector(
            entity_id=entity_id,
            answer_vector=answer_vector,
            category_id=category_id or "",
            tags=tags or [],
            difficulty=difficulty or "medium",
        )
        logger.info(f"Updated vector for entity {entity_id}")

    async def delete_vector(self, entity_id: str) -> None:
        """Soft-delete a vector by setting is_deleted=True."""
        try:
            expr = f'id == "{entity_id}"'
            self.collection.delete(expr)
            logger.info(f"Soft-deleted vector for entity {entity_id}")
        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            raise MilvusException(f"Vector deletion failed: {e}")

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        category_id: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[dict]:
        """Search for similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return.
            filter_expr: Custom filter expression.
            category_id: Optional category filter.
            difficulty: Optional difficulty filter.

        Returns:
            List of search results with id, similarity, and metadata.
        """
        try:
            # Build filter expression
            expr_parts = ["is_deleted == false"]
            if category_id:
                expr_parts.append(f'category_id == "{category_id}"')
            if difficulty:
                expr_parts.append(f'difficulty == "{difficulty}"')
            if filter_expr:
                expr_parts.append(filter_expr)
            expr = " && ".join(expr_parts)

            results = self.collection.search(
                data=[query_vector],
                anns_field="answer_vector",
                param={"metric_type": "COSINE", "params": {"nprobe": 16}},
                limit=top_k,
                expr=expr,
                output_fields=["id", "category_id", "tags", "difficulty", "version"],
            )

            formatted = []
            for hits in results:
                for hit in hits:
                    formatted.append({
                        "id": hit.id,
                        "similarity": hit.distance,
                        "category_id": hit.entity.get("category_id", ""),
                        "tags": hit.entity.get("tags", []),
                        "difficulty": hit.entity.get("difficulty", "medium"),
                        "version": hit.entity.get("version", 1),
                    })
            logger.debug(f"Search returned {len(formatted)} results")
            return formatted
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise MilvusException(f"Vector search failed: {e}")

    async def count(self) -> int:
        """Get total entity count (excluding soft-deleted)."""
        try:
            self.collection.load()
            return self.collection.query(
                expr="is_deleted == false",
                output_fields=["count(*)"],
            )[0].get("count(*)", 0)
        except Exception as e:
            logger.error(f"Failed to count entities: {e}")
            return 0
