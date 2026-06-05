"""FastAPI dependency injection providers.

Provides factory functions for all services, agents, and the agentic RAG
retriever. Multi-agent components are lazily initialized only when the
feature flag (multi_agent_enabled) is active.
"""

from typing import AsyncGenerator, Optional

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

# Lazy imports for multi-agent components (avoid loading at startup)
# These are imported only when get_*_agent() is first called


# ---- Settings ----

def get_settings_dep() -> Settings:
    return get_settings()


# ---- Database (alias for convenience) ----
get_db = get_db_session


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


def get_resume_service(
    db: AsyncSession = Depends(get_db_session),
    minio_svc: MinioService = Depends(get_minio_service),
    ocr_svc: OcrService = Depends(get_ocr_service),
) -> ResumeService:
    return ResumeService(db_session=db, minio_service=minio_svc, ocr_service=ocr_svc)


def get_interview_service(
    db: AsyncSession = Depends(get_db_session),
) -> InterviewService:
    return InterviewService(db_session=db)


def get_kb_service(
    db: AsyncSession = Depends(get_db_session),
    milvus_svc: MilvusService = Depends(get_milvus_service),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(
        db_session=db,
        milvus_service=milvus_svc,
        embedding_service=embedding_svc,
    )


# ============================================================================
# Multi-Agent & Agentic RAG Providers
# ============================================================================
# These providers are lazily initialized. The agents and agentic retriever
# are only constructed when the multi_agent_enabled feature flag is True.


def get_hybrid_retriever(
    milvus_svc: MilvusService = Depends(get_milvus_service),
    embedding_svc: EmbeddingService = Depends(get_embedding_service),
):
    """Get the HybridRetriever for dense + sparse retrieval."""
    from app.rag.hybrid_retriever import HybridRetriever
    return HybridRetriever(
        milvus_service=milvus_svc,
        embedding_service=embedding_svc,
    )


def get_reranker(
    settings: Settings = Depends(get_settings_dep),
):
    """Get the LLM-based Reranker.

    Uses a lightweight LLM for cross-encoder scoring when multi-agent
    mode is enabled. Falls back to cosine similarity when disabled.
    """
    from app.rag.reranker import Reranker
    from app.agents.agent_factory import create_agentic_llm

    if settings.multi_agent_enabled:
        llm = create_agentic_llm(settings)
        return Reranker(llm=llm)
    return Reranker()  # Cosine similarity fallback


def get_agentic_retriever(
    settings: Settings = Depends(get_settings_dep),
    hybrid_retriever=Depends(get_hybrid_retriever),
    reranker=Depends(get_reranker),
):
    """Get the AgenticRetriever with 7-step agentic RAG loop.

    Only uses LLM-powered agentic decisions when multi_agent_enabled=True.
    """
    from app.rag.agentic_retriever import AgenticRetriever
    from app.agents.agent_factory import create_agentic_llm

    llm = create_agentic_llm(settings) if settings.multi_agent_enabled else None

    return AgenticRetriever(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
        llm=llm,  # None = skip agentic decisions, direct retrieval
        max_retry_attempts=settings.agentic_rag_max_retries,
        relevance_threshold=settings.agentic_rag_relevance_threshold,
        top_k=settings.agentic_rag_top_k,
    )
