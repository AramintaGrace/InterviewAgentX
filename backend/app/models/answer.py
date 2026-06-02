"""Answer and AnswerAnalysis models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.question import Question


class Answer(Base, UUIDMixin, SoftDeleteMixin):
    __tablename__ = "answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    audio_minio_key: Mapped[Optional[str]] = mapped_column(String(500))
    audio_duration_sec: Mapped[Optional[int]] = mapped_column(Integer)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    question: Mapped["Question"] = relationship("Question", back_populates="answers")
    analysis: Mapped[Optional["AnswerAnalysis"]] = relationship(
        "AnswerAnalysis", back_populates="answer", uselist=False
    )


class AnswerAnalysis(Base, UUIDMixin, SoftDeleteMixin):
    __tablename__ = "answer_analyses"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    eval_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    analysis_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    agent_model: Mapped[str] = mapped_column(String(100), nullable=False, default="deepseek-chat")
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    processing_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    answer: Mapped["Answer"] = relationship("Answer", back_populates="analysis")
