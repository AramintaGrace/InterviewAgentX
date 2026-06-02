"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- Application ----
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8080"

    # ---- PostgreSQL ----
    database_url: str = "postgresql+asyncpg://iax_user:changeme@localhost:5432/interview_agent"
    database_url_sync: str = "postgresql+psycopg2://iax_user:changeme@localhost:5432/interview_agent"

    # ---- Milvus ----
    milvus_host: str = "localhost"
    milvus_port: str = "19530"
    milvus_collection: str = "knowledge_base_vectors"

    # ---- MinIO ----
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_resumes: str = "resumes"
    minio_bucket_audio: str = "interview-audio"
    minio_secure: bool = False

    # ---- DeepSeek API ----
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model_chat: str = "deepseek-chat"
    deepseek_model_reasoner: str = "deepseek-reasoner"

    # ---- Embedding (硅基流动 SiliconFlow) ----
    embedding_api_key: str = ""  # 硅基流动 API Key
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    embedding_dim: int = 4096  # Qwen3-Embedding-8B 的默认维度

    # ---- OCR API (硅基流动 deepseek-ai/DeepSeek-OCR) ----
    ocr_api_key: str = ""  # 硅基流动 API Key
    ocr_base_url: str = "https://api.siliconflow.cn/v1"
    ocr_model: str = "deepseek-ai/DeepSeek-OCR"

    # ---- STT API (硅基流动 FunAudioLLM/SenseVoiceSmall) ----
    stt_api_key: str = ""
    stt_base_url: str = "https://api.siliconflow.cn/v1"
    stt_model: str = "FunAudioLLM/SenseVoiceSmall"

    # ---- Proxy ----
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: str = "localhost,127.0.0.1,postgres,milvus,minio,etcd"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
