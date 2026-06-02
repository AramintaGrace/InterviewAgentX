"""Knowledge Base service — dual-write orchestration (PostgreSQL + Milvus)."""

import logging
import uuid
from typing import List, Optional, Literal

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KBItem, KBCategory
from app.services.embedding_service import EmbeddingService
from app.services.milvus_service import MilvusService
from app.utils.exceptions import KnowledgeBaseException, NotFoundException

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service managing knowledge base CRUD with PostgreSQL + Milvus dual-write."""

    def __init__(self, db_session: AsyncSession, milvus_service: MilvusService,
                 embedding_service: EmbeddingService):
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

    async def update_category(self, cat_id: uuid.UUID, name: Optional[str] = None,
                              description: Optional[str] = None,
                              sort_order: Optional[int] = None) -> KBCategory:
        result = await self.db.execute(
            select(KBCategory).where(KBCategory.id == cat_id, KBCategory.is_deleted == False)
        )
        cat = result.scalar_one_or_none()
        if not cat:
            raise NotFoundException(f"分类 {cat_id} 不存在")
        if name is not None:
            cat.name = name
        if description is not None:
            cat.description = description
        if sort_order is not None:
            cat.sort_order = sort_order
        await self.db.commit()
        await self.db.refresh(cat)
        return cat

    async def delete_category(self, cat_id: uuid.UUID, keep_items: bool = True) -> dict:
        """删除分类。

        Args:
            cat_id: 分类 ID
            keep_items: True=保留条目（置空 category_id），False=级联软删除所有条目
        """
        result = await self.db.execute(
            select(KBCategory).where(KBCategory.id == cat_id, KBCategory.is_deleted == False)
        )
        cat = result.scalar_one_or_none()
        if not cat:
            raise NotFoundException(f"分类 {cat_id} 不存在")

        cat_name = cat.name
        items_deleted = 0

        if keep_items:
            # 保留条目，清空分类关联
            await self.db.execute(
                update(KBItem).where(KBItem.category_id == cat_id).values(category_id=None)
            )
        else:
            # 级联删除条目及其向量
            items_result = await self.db.execute(
                select(KBItem).where(KBItem.category_id == cat_id, KBItem.is_deleted == False)
            )
            items = items_result.scalars().all()
            for item in items:
                item.is_deleted = True
                items_deleted += 1
                try:
                    await self.milvus.delete_vector(str(item.id))
                except Exception:
                    pass

        cat.is_deleted = True
        await self.db.commit()
        logger.info(f"Deleted category '{cat_name}', keep_items={keep_items}, items_deleted={items_deleted}")
        return {"category_name": cat_name, "items_deleted": items_deleted, "items_kept": keep_items}

    # ---- Items ----

    async def create_item(self, question: str, answer: str,
                          category_id: Optional[uuid.UUID] = None,
                          title: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          difficulty: str = "medium") -> KBItem:
        item = KBItem(question=question, answer=answer, category_id=category_id,
                      title=title,
                      tags=tags or [], difficulty=difficulty, is_vectorized=False)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        try:
            vector = await self.embeddings.embed_text(answer)
            await self.milvus.insert_vector(
                entity_id=str(item.id), answer_vector=vector,
                category_id=str(category_id) if category_id else "",
                tags=tags or [], difficulty=difficulty,
            )
            item.is_vectorized = True
            await self.db.commit()
        except Exception as e:
            logger.error(f"Milvus insert failed for {item.id}: {e}")
        return item

    async def get_item(self, item_id: uuid.UUID) -> KBItem:
        result = await self.db.execute(
            select(KBItem).where(KBItem.id == item_id, KBItem.is_deleted == False)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(f"KB item {item_id} not found")
        return item

    async def list_items(self, category_id: Optional[uuid.UUID] = None,
                         search: Optional[str] = None, tag: Optional[str] = None,
                         difficulty: Optional[str] = None,
                         vectorization_status: Optional[str] = None,
                         page: int = 1, page_size: int = 20) -> tuple[List[KBItem], int]:
        query = select(KBItem).where(KBItem.is_deleted == False)
        count_query = select(func.count(KBItem.id)).where(KBItem.is_deleted == False)

        if category_id:
            query = query.where(KBItem.category_id == category_id)
            count_query = count_query.where(KBItem.category_id == category_id)
        if search:
            query = query.where(
                KBItem.title.ilike(f"%{search}%") | KBItem.question.ilike(f"%{search}%") | KBItem.answer.ilike(f"%{search}%")
            )
            count_query = count_query.where(
                KBItem.title.ilike(f"%{search}%") | KBItem.question.ilike(f"%{search}%") | KBItem.answer.ilike(f"%{search}%")
            )
        if tag:
            query = query.where(KBItem.tags.any(tag))
            count_query = count_query.where(KBItem.tags.any(tag))
        if difficulty:
            query = query.where(KBItem.difficulty == difficulty)
            count_query = count_query.where(KBItem.difficulty == difficulty)
        if vectorization_status:
            if vectorization_status == "vectorized":
                query = query.where(KBItem.is_vectorized == True, KBItem.needs_revectorize == False)
                count_query = count_query.where(KBItem.is_vectorized == True, KBItem.needs_revectorize == False)
            elif vectorization_status == "not_vectorized":
                query = query.where(KBItem.is_vectorized == False, KBItem.needs_revectorize == False)
                count_query = count_query.where(KBItem.is_vectorized == False, KBItem.needs_revectorize == False)
            elif vectorization_status == "needs_revectorize":
                query = query.where(KBItem.needs_revectorize == True)
                count_query = count_query.where(KBItem.needs_revectorize == True)

        total = (await self.db.execute(count_query)).scalar() or 0
        offset = (page - 1) * page_size
        query = query.order_by(KBItem.updated_at.desc()).offset(offset).limit(page_size)
        return list((await self.db.execute(query)).scalars().all()), total

    async def update_item(self, item_id: uuid.UUID, question: Optional[str] = None,
                          answer: Optional[str] = None, category_id: Optional[uuid.UUID] = None,
                          title: Optional[str] = None,
                          tags: Optional[List[str]] = None, difficulty: Optional[str] = None) -> KBItem:
        item = await self.get_item(item_id)
        if title is not None:
            item.title = title
        if question is not None:
            item.question = question
        answer_changed = False
        if answer is not None:
            item.answer = answer
            item.needs_revectorize = True
            item.is_vectorized = False
            answer_changed = True
        if category_id is not None:
            item.category_id = category_id
        if tags is not None:
            item.tags = tags
        if difficulty is not None:
            item.difficulty = difficulty
        item.version += 1
        await self.db.commit()
        await self.db.refresh(item)

        if answer_changed:
            try:
                await self._do_revectorize(item)
            except Exception as e:
                logger.error(f"Auto re-vectorize failed for {item.id}: {e}")
        return item

    async def delete_item(self, item_id: uuid.UUID) -> None:
        item = await self.get_item(item_id)
        item.is_deleted = True
        await self.db.commit()
        try:
            await self.milvus.delete_vector(str(item.id))
        except Exception as e:
            logger.error(f"Milvus soft-delete failed for {item.id}: {e}")

    async def revectorize_item(self, item_id: uuid.UUID) -> KBItem:
        item = await self.get_item(item_id)
        await self._do_revectorize(item)
        await self.db.refresh(item)
        return item

    async def _do_revectorize(self, item: KBItem) -> None:
        vector = await self.embeddings.embed_text(item.answer)
        await self.milvus.update_vector(
            entity_id=str(item.id), answer_vector=vector,
            category_id=str(item.category_id) if item.category_id else "",
            tags=item.tags or [], difficulty=item.difficulty,
        )
        item.is_vectorized = True
        item.needs_revectorize = False
        await self.db.commit()

    # ---- Batch operations ----

    async def batch_delete_items(self, item_ids: List[uuid.UUID]) -> int:
        count = 0
        for iid in item_ids:
            try:
                await self.delete_item(iid)
                count += 1
            except NotFoundException:
                pass
        return count

    async def batch_revectorize(self, item_ids: List[uuid.UUID]) -> dict:
        success, failed = [], []
        for iid in item_ids:
            try:
                await self.revectorize_item(iid)
                success.append(str(iid))
            except Exception as e:
                failed.append({"id": str(iid), "error": str(e)})
        return {"success": len(success), "failed": len(failed), "failed_details": failed}

    async def batch_update_category(self, item_ids: List[uuid.UUID],
                                    category_id: Optional[uuid.UUID]) -> int:
        if category_id:
            # 验证分类存在
            cr = await self.db.execute(
                select(KBCategory).where(KBCategory.id == category_id, KBCategory.is_deleted == False)
            )
            if not cr.scalar_one_or_none():
                raise NotFoundException(f"分类 {category_id} 不存在")
        count = 0
        for iid in item_ids:
            try:
                item = await self.get_item(iid)
                item.category_id = category_id
                count += 1
            except NotFoundException:
                pass
        await self.db.commit()
        return count
