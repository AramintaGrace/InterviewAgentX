"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
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

    # Register routes
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "InterviewAgentX"}

    return app


app = create_app()
