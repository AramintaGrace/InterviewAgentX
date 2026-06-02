"""Interview session management service."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interview session lifecycle."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_session(
        self,
        candidate_id: uuid.UUID,
        resume_id: uuid.UUID,
        question_source: str,
        total_questions: int = 5,
    ) -> InterviewSession:
        """Create a new interview session."""
        thread_id = f"interview-{uuid.uuid4().hex[:12]}"

        session = InterviewSession(
            candidate_id=candidate_id,
            resume_id=resume_id,
            langgraph_thread_id=thread_id,
            status="created",
            question_source=question_source,
            total_questions=total_questions,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"Created interview session {session.id} with thread {thread_id}")
        return session

    async def get_session(self, session_id: uuid.UUID) -> InterviewSession:
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.is_deleted == False,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Interview session {session_id} not found")
        return session

    async def start_session(self, session_id: uuid.UUID) -> InterviewSession:
        session = await self.get_session(session_id)
        session.status = "in_progress"
        session.started_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def complete_session(
        self,
        session_id: uuid.UUID,
        total_score: Optional[float] = None,
    ) -> InterviewSession:
        session = await self.get_session(session_id)
        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        if total_score is not None:
            session.total_score = total_score
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_by_thread(self, thread_id: str) -> InterviewSession:
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.langgraph_thread_id == thread_id,
                InterviewSession.is_deleted == False,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session with thread {thread_id} not found")
        return session
