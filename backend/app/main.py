"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.utils.exceptions import (
    InterviewAgentXException,
    NotFoundException,
    OCRException,
    STTException,
    MilvusException,
    MinIOException,
    AgentException,
    KnowledgeBaseException,
)
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    logger = setup_logger(settings.log_level)
    logger.info(f"Starting InterviewAgentX in {settings.environment} mode")

    # Initialize MinIO buckets on startup
    from app.services.minio_service import MinioService
    minio_svc = MinioService(settings)
    await minio_svc.ensure_buckets()

    yield

    logger.info("Shutting down InterviewAgentX")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="InterviewAgentX",
        description="智能面试辅助系统 - Intelligent Interview Assistant System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Global exception handlers ----

    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "code": exc.code},
        )

    @app.exception_handler(OCRException)
    async def ocr_error_handler(request: Request, exc: OCRException):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": exc.code},
        )

    @app.exception_handler(MinIOException)
    async def minio_error_handler(request: Request, exc: MinIOException):
        return JSONResponse(
            status_code=500,
            content={"detail": f"文件存储失败: {exc}", "code": exc.code},
        )

    @app.exception_handler(MilvusException)
    async def milvus_error_handler(request: Request, exc: MilvusException):
        return JSONResponse(
            status_code=500,
            content={"detail": f"向量数据库错误: {exc}", "code": exc.code},
        )

    @app.exception_handler(STTException)
    async def stt_error_handler(request: Request, exc: STTException):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": exc.code},
        )

    @app.exception_handler(AgentException)
    async def agent_error_handler(request: Request, exc: AgentException):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "code": exc.code},
        )

    @app.exception_handler(KnowledgeBaseException)
    async def kb_error_handler(request: Request, exc: KnowledgeBaseException):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger = setup_logger(settings.log_level)
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"服务器内部错误: {exc}",
                "code": "INTERNAL_ERROR",
            },
        )

    # Register routes
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "InterviewAgentX"}

    return app


app = create_app()
