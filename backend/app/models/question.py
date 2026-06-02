"""Question model."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.interview_session import InterviewSession
    from app.models.knowledge_base import KBItem
    from app.models.answer import Answer


class Question(Base, UUIDMixin, SoftDeleteMixin):
    __tablename__ = "questions"

    interview_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_kb_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kb_items.id", ondelete="SET NULL")
    )
    source_resume_context: Mapped[Optional[str]] = mapped_column(Text)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_reference_answer: Mapped[Optional[str]] = mapped_column(Text)
    question_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[str] = mapped_column(Text)  # Handled by DB default

    interview_session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="questions"
    )
    source_kb_item: Mapped[Optional["KBItem"]] = relationship(
        "KBItem", back_populates="questions"
    )
    answers: Mapped[List["Answer"]] = relationship(
        "Answer", back_populates="question", lazy="selectin"
    )
