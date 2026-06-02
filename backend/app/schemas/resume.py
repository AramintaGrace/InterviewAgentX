"""Resume-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    current_role: Optional[str] = Field(None, max_length=200)
    years_of_exp: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class CandidateResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    years_of_exp: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    id: UUID
    file_name: str
    file_size_bytes: int
    mime_type: str
    ocr_status: str
    ocr_error_msg: Optional[str] = None
    ocr_raw_text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    id: UUID
    candidate_id: Optional[UUID] = None
    file_name: str
    file_size_bytes: int
    mime_type: str
    ocr_status: str
    ocr_raw_text: Optional[str] = None
    ocr_error_msg: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeAnalysisResponse(BaseModel):
    id: UUID
    resume_id: UUID
    agent_model: str
    analysis_json: Dict[str, Any]
    tokens_used: Optional[int] = None
    processing_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
