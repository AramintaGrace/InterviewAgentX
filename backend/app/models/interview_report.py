"""InterviewReport model."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.interview_session import InterviewSession


class InterviewReport(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "interview_reports"

    interview_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    report_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    agent_model: Mapped[str] = mapped_column(String(100), nullable=False, default="deepseek-chat")
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    processing_ms: Mapped[Optional[int]] = mapped_column(Integer)

    interview_session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="report"
    )
