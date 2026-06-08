"""
core/database.py
-----------------
PostgreSQL / SQLite connection manager menggunakan SQLAlchemy async.

Tables:
  - orders         → data order lengkap dari supply chain
  - order_items     → detail item per order
  - predictions     → log hasil prediksi risk model
  - forecast_logs   → log hasil demand forecast
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def connect(self):
        logger.info(f"Connecting to Database: {settings.DATABASE_URL}")
        
        # --- PERUBAHAN DI SINI: Argumen Dasar untuk Semua Database ---
        engine_kwargs = {
            "echo": settings.DEBUG,
        }

        # Pooling arguments (pool_size, max_overflow) HANYA untuk PostgreSQL
        if settings.DATABASE_URL.startswith("postgresql"):
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20
        # -------------------------------------------------------------

        self.engine = create_async_engine(
            settings.DATABASE_URL,
            **engine_kwargs  # Masukkan argumen yang sudah disaring
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables if they don't exist
        from backend.schemas.db_models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected and tables ensured.")

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed.")


database = Database()


async def get_db() -> AsyncSession:
    """FastAPI dependency — inject ke router."""
    async with database.async_session() as session:
        yield session