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


class KBSourceConfig(BaseModel):
    """单个分类的题目配置。"""
    category_id: Optional[UUID] = None  # None = 不限分类
    count: int = Field(default=2, ge=0, le=20)


class QuestionGenerateRequest(BaseModel):
    source: Literal["resume", "knowledge_base", "mixed"] = "resume"
    count: int = Field(default=5, ge=1, le=20)
    # KB/mixed 模式：按分类指定题目数，为空则从全部分类随机
    kb_configs: List[KBSourceConfig] = Field(default_factory=list)
    # mixed 模式：resume 占比（0-100），如 60 表示 60% resume + 40% KB
    resume_ratio: int = Field(default=60, ge=0, le=100)
    # 题目池：这些题库条目的 ID 保证出现在面试题中（已向量化的 KB 条目）
    pool_ids: List[UUID] = Field(default_factory=list)


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
