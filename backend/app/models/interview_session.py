"""InterviewSession model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.resume import Resume
    from app.models.question import Question
    from app.models.interview_report import InterviewReport


class InterviewSession(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "interview_sessions"

    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL")
    )
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL")
    )
    langgraph_thread_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created")
    question_source: Mapped[Optional[str]] = mapped_column(String(30))
    total_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    completed_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    total_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    candidate: Mapped[Optional["Candidate"]] = relationship(
        "Candidate", back_populates="interview_sessions"
    )
    resume: Mapped[Optional["Resume"]] = relationship("Resume")
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="interview_session", lazy="selectin"
    )
    report: Mapped[Optional["InterviewReport"]] = relationship(
        "InterviewReport", back_populates="interview_session", uselist=False
    )
