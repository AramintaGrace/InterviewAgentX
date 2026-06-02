"""Interview-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewSessionCreate(BaseModel):
    candidate_id: UUID
    resume_id: UUID
    question_source: Literal["resume", "knowledge_base", "mixed"]
    total_questions: int = Field(default=5, ge=1, le=20)


class InterviewSessionResponse(BaseModel):
    id: UUID
    candidate_id: Optional[UUID] = None
    resume_id: Optional[UUID] = None
    langgraph_thread_id: str
    status: str
    question_source: Optional[str] = None
    total_questions: int
    completed_questions: int
    total_score: Optional[Decimal] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionGenerateRequest(BaseModel):
    source: Literal["resume", "knowledge_base", "mixed"] = "resume"
    count: int = Field(default=5, ge=1, le=20)
    category_id: Optional[UUID] = None  # For knowledge_base source
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None


class QuestionResponse(BaseModel):
    id: UUID
    interview_session_id: UUID
    source_type: str
    source_kb_item_id: Optional[UUID] = None
    source_resume_context: Optional[str] = None
    question_text: str
    ai_reference_answer: Optional[str] = None
    question_order: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    transcript_text: str
    audio_minio_key: Optional[str] = None
    audio_duration_sec: Optional[int] = None


class AnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    transcript_text: str
    audio_minio_key: Optional[str] = None
    audio_duration_sec: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerAnalysisResponse(BaseModel):
    id: UUID
    answer_id: UUID
    question_id: UUID
    eval_mode: str
    analysis_json: Dict[str, Any]
    agent_model: str
    tokens_used: Optional[int] = None
    processing_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewStateResponse(BaseModel):
    """Debug response showing full LangGraph state."""
    state: Dict[str, Any]
