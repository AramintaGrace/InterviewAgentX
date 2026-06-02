"""Knowledge Base models: KBCategory and KBItem."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.question import Question


class KBCategory(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "kb_categories"

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kb_categories.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    parent: Mapped[Optional["KBCategory"]] = relationship(
        "KBCategory", remote_side="KBCategory.id", back_populates="children"
    )
    children: Mapped[List["KBCategory"]] = relationship(
        "KBCategory", back_populates="parent", lazy="selectin"
    )
    items: Mapped[List["KBItem"]] = relationship(
        "KBItem", back_populates="category", lazy="selectin"
    )


class KBItem(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "kb_items"

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kb_categories.id", ondelete="SET NULL")
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(Text), default=list)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False, default="text-embedding-3-small")
    embedding_dim: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1536)
    is_vectorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    category: Mapped[Optional["KBCategory"]] = relationship(
        "KBCategory", back_populates="items"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="source_kb_item", lazy="selectin"
    )
