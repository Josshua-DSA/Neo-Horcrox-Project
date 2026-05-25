"""
app/backend/core/database.py
-----------------
PostgreSQL connection manager menggunakan SQLAlchemy async + asyncpg.
"""

from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from ..config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def connect(self):
        logger.info(f"Connecting to PostgreSQL: {settings.DATABASE_URL}")
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        # Create tables if they don't exist
        from ..schemas.db_models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL connected and tables ensured.")

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL connection closed.")


database = Database()


async def get_db() -> AsyncSession:
    """FastAPI dependency — inject ke router."""
    async with database.async_session() as session:
        yield session
