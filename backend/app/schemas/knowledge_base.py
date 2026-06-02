"""Knowledge Base Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KBCategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    sort_order: int = 0


class KBCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class KBCategoryResponse(BaseModel):
    id: UUID
    parent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KBItemCreate(BaseModel):
    category_id: Optional[UUID] = None
    title: Optional[str] = Field(None, max_length=300)
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class KBItemUpdate(BaseModel):
    category_id: Optional[UUID] = None
    title: Optional[str] = Field(None, max_length=300)
    question: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")


class KBItemResponse(BaseModel):
    id: UUID
    category_id: Optional[UUID] = None
    title: Optional[str] = None
    question: str
    answer: str
    tags: Optional[List[str]] = None
    difficulty: str
    embedding_model: str
    embedding_dim: int
    is_vectorized: bool
    needs_revectorize: bool = False
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchOperationRequest(BaseModel):
    item_ids: List[UUID] = Field(..., min_length=1)
    category_id: Optional[UUID] = None  # for batch update category

