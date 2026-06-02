"""LangGraph checkpointer using PostgreSQL."""

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import Settings

logger = logging.getLogger(__name__)


checkpointer_instance: Optional[AsyncPostgresSaver] = None


async def get_checkpointer(settings: Settings) -> AsyncPostgresSaver:
    """Create or return the singleton AsyncPostgresSaver instance."""
    global checkpointer_instance

    if checkpointer_instance is not None:
        return checkpointer_instance

    checkpointer = AsyncPostgresSaver.from_conn_string(settings.database_url)
    await checkpointer.setup()
    checkpointer_instance = checkpointer
    logger.info("LangGraph AsyncPostgresSaver initialized")
    return checkpointer_instance


async def close_checkpointer() -> None:
    """Close the checkpointer connection."""
    global checkpointer_instance
    if checkpointer_instance:
        await checkpointer_instance.aclose()
        checkpointer_instance = None
