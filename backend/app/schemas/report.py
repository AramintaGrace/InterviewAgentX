"""Interview report Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    id: UUID
    interview_session_id: UUID
    report_json: Dict[str, Any]
    agent_model: str
    tokens_used: Optional[int] = None
    processing_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewRecordResponse(BaseModel):
    candidate_id: UUID
    candidate_name: str
    candidate_email: Optional[str] = None
    resume_id: Optional[UUID] = None
    session_id: UUID
    interview_date: datetime
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
