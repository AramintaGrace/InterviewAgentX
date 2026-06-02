"""Resume processing service."""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeAnalysis
from app.services.minio_service import MinioService
from app.services.ocr_service import OcrService

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume upload, OCR processing, and analysis."""

    def __init__(
        self,
        db_session: AsyncSession,
        minio_service: MinioService,
        ocr_service: OcrService,
    ):
        self.db = db_session
        self.minio = minio_service
        self.ocr = ocr_service

    async def upload_resume(
        self,
        file_name: str,
        file_data: bytes,
        content_type: str,
        candidate_id: Optional[uuid.UUID] = None,
    ) -> Resume:
        """Upload a resume file to MinIO and create a database record.

        OCR is triggered asynchronously — the record starts with ocr_status='pending'.
        """
        object_key = f"resumes/{uuid.uuid4()}/{file_name}"

        # Upload to MinIO
        await self.minio.upload_file(
            bucket="resumes",
            object_key=object_key,
            file_data=file_data,
            content_type=content_type,
        )

        # Create DB record
        resume = Resume(
            candidate_id=candidate_id,
            file_name=file_name,
            file_size_bytes=len(file_data),
            mime_type=content_type,
            minio_bucket="resumes",
            minio_object_key=object_key,
            ocr_status="pending",
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        # Trigger OCR (synchronous for simplicity; could be background task)
        try:
            resume.ocr_status = "processing"
            await self.db.commit()

            ocr_text = await self.ocr.extract_text(file_data, file_name)
            resume.ocr_raw_text = ocr_text
            resume.ocr_status = "completed"

            # Try to parse structured info
            parsed = await self.ocr.parse_resume_info(ocr_text)
            resume.parsed_data = parsed

            await self.db.commit()
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            resume.ocr_status = "failed"
            resume.ocr_error_msg = str(e)
            await self.db.commit()

        await self.db.refresh(resume)
        return resume

    async def get_resume(self, resume_id: uuid.UUID) -> Resume:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.is_deleted == False)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")
        return resume

    async def save_analysis(
        self,
        resume_id: uuid.UUID,
        analysis_json: dict,
        agent_model: str = "deepseek-chat",
        tokens_used: Optional[int] = None,
        processing_ms: Optional[int] = None,
    ) -> ResumeAnalysis:
        """Save a resume analysis result."""
        analysis = ResumeAnalysis(
            resume_id=resume_id,
            agent_model=agent_model,
            analysis_json=analysis_json,
            tokens_used=tokens_used,
            processing_ms=processing_ms,
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
