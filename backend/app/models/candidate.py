"""Candidate model."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.interview_session import InterviewSession


class Candidate(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "candidates"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    current_role: Mapped[Optional[str]] = mapped_column(String(200))
    years_of_exp: Mapped[Optional[int]] = mapped_column(SmallInteger)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    resumes: Mapped[List["Resume"]] = relationship(
        "Resume", back_populates="candidate", lazy="selectin"
    )
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="candidate", lazy="selectin"
    )
