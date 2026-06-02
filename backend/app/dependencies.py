"""FastAPI dependency injection providers."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import Settings, get_settings
from app.db.postgresql import get_db_session
from app.services.minio_service import MinioService
from app.services.ocr_service import OcrService
from app.services.embedding_service import EmbeddingService
from app.services.milvus_service import MilvusService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.resume_service import ResumeService
from app.services.interview_service import InterviewService
from app.services.stt_service import STTService


# ---- Settings ----

async def get_settings_dep() -> Settings:
    return get_settings()


# ---- Database ----

async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    yield session


# ---- Services ----

def get_minio_service(settings: Settings = Depends(get_settings_dep)) -> MinioService:
    return MinioService(settings)


def get_ocr_service(settings: Settings = Depends(get_settings_dep)) -> OcrService:
    return OcrService(settings)


def get_embedding_service(settings: Settings = Depends(get_settings_dep)) -> EmbeddingService:
    return EmbeddingService(settings)


def get_milvus_service(settings: Settings = Depends(get_settings_dep)) -> MilvusService:
    return MilvusService(settings)


def get_stt_service(settings: Settings = Depends(get_settings_dep)) -> STTService:
    return STTService(settings)


async def get_resume_service(
    db: AsyncSession = Depends(get_db),
    minio_svc: MinioService = Depends(get_minio_service),
    ocr_svc: OcrService = Depends(get_ocr_service),
) -> ResumeService:
    return ResumeService(db_session=db, minio_service=minio_svc, ocr_service=ocr_svc)


async def get_interview_service(
    db: AsyncSession = Depends(get_db),
) -> InterviewService:
    return InterviewService(db_session=db)


async def get_kb_service(
    db: AsyncSession = Depends(get_db),
    milvus_svc: MilvusService = Depends(get_milvus_service),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(
        db_session=db,
        milvus_service=milvus_svc,
        embedding_service=embedding_svc,
    )
