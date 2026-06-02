"""Resume and ResumeAnalysis models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class Resume(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "resumes"

    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL")
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    minio_bucket: Mapped[str] = mapped_column(String(200), nullable=False, default="resumes")
    minio_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    ocr_raw_text: Mapped[Optional[str]] = mapped_column(Text)
    ocr_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    ocr_error_msg: Mapped[Optional[str]] = mapped_column(Text)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    candidate: Mapped[Optional["Candidate"]] = relationship(
        "Candidate", back_populates="resumes"
    )
    analyses: Mapped[list["ResumeAnalysis"]] = relationship(
        "ResumeAnalysis", back_populates="resume", lazy="selectin"
    )


class ResumeAnalysis(Base, UUIDMixin, SoftDeleteMixin):
    __tablename__ = "resume_analyses"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    agent_model: Mapped[str] = mapped_column(String(100), nullable=False, default="deepseek-chat")
    analysis_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    processing_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    resume: Mapped["Resume"] = relationship("Resume", back_populates="analyses")
