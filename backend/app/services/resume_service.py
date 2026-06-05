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

            # 如果没有指定候选人且 OCR 解析出了姓名，自动创建候选人
            if not candidate_id and parsed and parsed.get("name"):
                candidate = await self._find_or_create_candidate(
                    name=parsed["name"],
                    email=parsed.get("email"),
                    phone=parsed.get("phone"),
                )
                resume.candidate_id = candidate.id
                logger.info(f"Auto-created candidate: {candidate.name} ({candidate.id})")

            await self.db.commit()
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            resume.ocr_status = "failed"
            resume.ocr_error_msg = str(e)
            await self.db.commit()

        await self.db.refresh(resume)
        return resume

    async def _find_or_create_candidate(
        self, name: str, email: Optional[str], phone: Optional[str]
    ):
        """Find existing candidate by email/phone or create a new one."""
        from sqlalchemy import select, or_
        from app.models.candidate import Candidate

        # 尝试按邮箱或电话查找已有候选人
        conditions = []
        if email:
            conditions.append(Candidate.email == email)
        if phone:
            conditions.append(Candidate.phone == phone)

        if conditions:
            result = await self.db.execute(
                select(Candidate).where(
                    or_(*conditions),
                    Candidate.is_deleted == False,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info(f"Found existing candidate by contact: {existing.name}")
                return existing

        # 新建候选人
        candidate = Candidate(name=name, email=email, phone=phone)
        self.db.add(candidate)
        await self.db.flush()  # 获取 ID 但不提交（由外层统一 commit）
        return candidate

    async def get_resume(self, resume_id: uuid.UUID) -> Resume:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.is_deleted == False)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")
        return resume

    async def upload_multiple_images(
        self,
        files: list[tuple[str, bytes, str]],
        candidate_id: Optional[uuid.UUID] = None,
    ) -> Resume:
        """Upload multiple resume images, OCR each, then merge into one coherent resume.

        Flow:
          1. Upload each image to MinIO
          2. OCR each image independently
          3. Direct concatenation (no content loss) + optional LLM dedup
          4. Parse structured info from merged text
          5. Create single Resume record with merged text
        """
        if not files:
            raise ValueError("At least one file required")

        # Step 1: Upload all files to MinIO
        object_keys = []
        for file_name, file_data, content_type in files:
            object_key = f"resumes/{uuid.uuid4()}/{file_name}"
            await self.minio.upload_file(
                bucket="resumes",
                object_key=object_key,
                file_data=file_data,
                content_type=content_type,
            )
            object_keys.append(object_key)

        # Step 2: OCR each image independently
        ocr_results = []      # (file_name, text)
        ocr_errors = []
        for file_name, file_data, _ in files:
            try:
                text = await self.ocr.extract_text(file_data, file_name)
                if text.strip():
                    ocr_results.append((file_name, text))
                    logger.info(f"OCR: {file_name} → {len(text)} chars")
            except Exception as e:
                logger.warning(f"OCR failed for {file_name}: {e}")
                ocr_errors.append(f"{file_name}: {e}")

        if not ocr_results:
            raise ValueError("All OCR attempts failed. Check file quality and try again.")

        # Step 3: Always direct concatenation — zero content loss guaranteed.
        # Each page's OCR text is preserved as-is with clear dividers.
        if len(ocr_results) == 1:
            merged_text = ocr_results[0][1]
        else:
            parts = []
            for i, (fname, text) in enumerate(ocr_results):
                parts.append(f"=== 第{i+1}页 ({fname}) ===\n{text}")
            merged_text = "\n\n".join(parts)
            logger.info(
                f"Direct concatenation: {len(ocr_results)} pages, "
                f"{sum(len(t) for _, t in ocr_results)} chars total → "
                f"{len(merged_text)} chars merged"
            )

        # Step 4: Create unified resume record
        primary_file = files[0]
        resume = Resume(
            candidate_id=candidate_id,
            file_name=f"merged_{len(files)}pages_{primary_file[0]}",
            file_size_bytes=sum(len(f[1]) for f in files),
            mime_type=primary_file[2],
            minio_bucket="resumes",
            minio_object_key=object_keys[0],
            ocr_status="processing",
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        try:
            resume.ocr_status = "processing"
            await self.db.commit()

            resume.ocr_raw_text = merged_text
            resume.ocr_status = "completed"

            parsed = await self.ocr.parse_resume_info(merged_text)
            resume.parsed_data = parsed

            if not candidate_id and parsed and parsed.get("name"):
                candidate = await self._find_or_create_candidate(
                    name=parsed["name"],
                    email=parsed.get("email"),
                    phone=parsed.get("phone"),
                )
                resume.candidate_id = candidate.id

            await self.db.commit()
        except Exception as e:
            logger.error(f"Merge/parse failed: {e}")
            resume.ocr_status = "failed"
            resume.ocr_error_msg = str(e)
            await self.db.commit()

        await self.db.refresh(resume)
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
