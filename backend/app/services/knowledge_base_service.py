"""Knowledge Base service — dual-write orchestration (PostgreSQL + Milvus)."""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KBItem, KBCategory
from app.services.embedding_service import EmbeddingService
from app.services.milvus_service import MilvusService
from app.utils.exceptions import KnowledgeBaseException, NotFoundException

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service managing knowledge base CRUD with PostgreSQL + Milvus dual-write."""

    def __init__(
        self,
        db_session: AsyncSession,
        milvus_service: MilvusService,
        embedding_service: EmbeddingService,
    ):
        self.db = db_session
        self.milvus = milvus_service
        self.embeddings = embedding_service

    # ---- Categories ----

    async def create_category(self, name: str, parent_id: Optional[uuid.UUID] = None,
                              description: Optional[str] = None) -> KBCategory:
        cat = KBCategory(name=name, parent_id=parent_id, description=description)
        self.db.add(cat)
        await self.db.commit()
        await self.db.refresh(cat)
        return cat

    async def list_categories(self) -> List[KBCategory]:
        result = await self.db.execute(
            select(KBCategory).where(KBCategory.is_deleted == False).order_by(KBCategory.sort_order)
        )
        return list(result.scalars().all())

    # ---- Items ----

    async def create_item(
        self,
        question: str,
        answer: str,
        category_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        difficulty: str = "medium",
    ) -> KBItem:
        """Create a KB item — write to PG, then vectorize and insert to Milvus.

        Transaction order: PG first (get ID), then Milvus. If Milvus fails,
        we mark the PG record as not vectorized so it can be retried.
        """
        item = KBItem(
            question=question,
            answer=answer,
            category_id=category_id,
            tags=tags or [],
            difficulty=difficulty,
            is_vectorized=False,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        try:
            # Generate embedding and insert to Milvus
            vector = await self.embeddings.embed_text(answer)
            await self.milvus.insert_vector(
                entity_id=str(item.id),
                answer_vector=vector,
                category_id=str(category_id) if category_id else "",
                tags=tags or [],
                difficulty=difficulty,
            )
            item.is_vectorized = True
            await self.db.commit()
            logger.info(f"Created KB item {item.id} with vector")
        except Exception as e:
            logger.error(f"Milvus insert failed for item {item.id}, marked as not vectorized: {e}")
            # Item exists in PG but not in Milvus — can be retried with revectorize

        return item

    async def get_item(self, item_id: uuid.UUID) -> KBItem:
        result = await self.db.execute(
            select(KBItem).where(KBItem.id == item_id, KBItem.is_deleted == False)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(f"KB item {item_id} not found")
        return item

    async def list_items(
        self,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        difficulty: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[KBItem], int]:
        query = select(KBItem).where(KBItem.is_deleted == False)
        count_query = select(func.count(KBItem.id)).where(KBItem.is_deleted == False)

        if category_id:
            query = query.where(KBItem.category_id == category_id)
            count_query = count_query.where(KBItem.category_id == category_id)
        if search:
            query = query.where(KBItem.question.ilike(f"%{search}%"))
            count_query = count_query.where(KBItem.question.ilike(f"%{search}%"))
        if tag:
            query = query.where(KBItem.tags.any(tag))
            count_query = count_query.where(KBItem.tags.any(tag))
        if difficulty:
            query = query.where(KBItem.difficulty == difficulty)
            count_query = count_query.where(KBItem.difficulty == difficulty)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(KBItem.updated_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_item(
        self,
        item_id: uuid.UUID,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> KBItem:
        """Update a KB item — update PG, then re-vectorize in Milvus if answer changed."""
        item = await self.get_item(item_id)

        if question is not None:
            item.question = question
        if answer is not None:
            item.answer = answer
            item.is_vectorized = False  # Will be re-vectorized
        if category_id is not None:
            item.category_id = category_id
        if tags is not None:
            item.tags = tags
        if difficulty is not None:
            item.difficulty = difficulty

        item.version += 1
        await self.db.commit()
        await self.db.refresh(item)

        # Re-vectorize if answer changed
        if answer is not None:
            try:
                vector = await self.embeddings.embed_text(item.answer)
                await self.milvus.update_vector(
                    entity_id=str(item.id),
                    answer_vector=vector,
                    category_id=str(item.category_id) if item.category_id else "",
                    tags=item.tags or [],
                    difficulty=item.difficulty,
                )
                item.is_vectorized = True
                await self.db.commit()
            except Exception as e:
                logger.error(f"Milvus update failed for item {item.id}: {e}")

        return item

    async def delete_item(self, item_id: uuid.UUID) -> None:
        """Soft-delete from both PG and Milvus."""
        item = await self.get_item(item_id)

        # Soft-delete in PG
        item.is_deleted = True
        await self.db.commit()

        # Soft-delete in Milvus
        try:
            await self.milvus.delete_vector(str(item.id))
        except Exception as e:
            logger.error(f"Milvus soft-delete failed for item {item.id}: {e}")
            # PG is already soft-deleted; Milvus search filters on is_deleted so
            # retry can happen later

    async def revectorize_item(self, item_id: uuid.UUID) -> KBItem:
        """Force re-vectorize a KB item that was not properly vectorized."""
        item = await self.get_item(item_id)
        try:
            vector = await self.embeddings.embed_text(item.answer)
            await self.milvus.update_vector(
                entity_id=str(item.id),
                answer_vector=vector,
                category_id=str(item.category_id) if item.category_id else "",
                tags=item.tags or [],
                difficulty=item.difficulty,
            )
            item.is_vectorized = True
            await self.db.commit()
            await self.db.refresh(item)
            return item
        except Exception as e:
            logger.error(f"Revectorize failed for item {item.id}: {e}")
            raise KnowledgeBaseException(f"Revectorization failed: {e}")
