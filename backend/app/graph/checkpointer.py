"""LangGraph checkpointer using PostgreSQL."""

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import Settings

logger = logging.getLogger(__name__)

checkpointer_instance: Optional[AsyncPostgresSaver] = None
_context_manager: Optional[object] = None


async def get_checkpointer(settings: Settings) -> AsyncPostgresSaver:
    """Create or return the singleton AsyncPostgresSaver instance.

    AsyncPostgresSaver.from_conn_string() 返回的是 async context manager，
    必须用 async with ... as saver: 进入才能拿到实际实例。
    """
    global checkpointer_instance, _context_manager

    if checkpointer_instance is not None:
        return checkpointer_instance

    # from_conn_string 不接受 +asyncpg 前缀，只接受标准 postgresql:// 或 postgres://
    checkpointer_url = settings.database_url.replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    cm = AsyncPostgresSaver.from_conn_string(checkpointer_url)
    saver = await cm.__aenter__()
    await saver.setup()

    checkpointer_instance = saver
    _context_manager = cm
    logger.info("LangGraph AsyncPostgresSaver initialized")
    return checkpointer_instance


async def close_checkpointer() -> None:
    """Close the checkpointer connection."""
    global checkpointer_instance, _context_manager
    if _context_manager:
        await _context_manager.__aexit__(None, None, None)
        _context_manager = None
    checkpointer_instance = None
