"""MongoDB connection manager used by FastAPI dependencies."""

from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """Small OOP wrapper around Motor so startup can be CI-friendly."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.last_error: str | None = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.db is not None

    async def connect(self) -> None:
        if not settings.MONGODB_ENABLED:
            logger.info("MongoDB is disabled by configuration.")
            return

        logger.info("Connecting to MongoDB at %s", settings.MONGODB_URI)
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
            )
            await self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DB_NAME]
            await self._create_indexes()
            self.last_error = None
            logger.info("Connected to MongoDB database %s", settings.MONGODB_DB_NAME)
        except Exception as exc:
            self.client = None
            self.db = None
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("MongoDB connection failed")
            if settings.MONGODB_REQUIRED:
                raise

    async def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.db = None

    def get_db(self) -> AsyncIOMotorDatabase | None:
        return self.db

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.MONGODB_ENABLED,
            "required": settings.MONGODB_REQUIRED,
            "connected": self.is_connected,
            "database": settings.MONGODB_DB_NAME,
            "last_error": self.last_error,
        }

    async def _create_indexes(self) -> None:
        if self.db is None:
            return
        await self.db.orders.create_index("order_id", unique=True)
        await self.db.orders.create_index("order_date")
        await self.db.orders.create_index("customer_id")
        await self.db.orders.create_index("late_delivery_risk")
        await self.db.orders.create_index("market")
        await self.db.orders.create_index("shipping_mode")
        await self.db.orders.create_index("category_name")
        await self.db.orders.create_index("product_card_id")

        await self.db.order_items.create_index("order_id")
        await self.db.order_items.create_index("order_item_id", unique=True)

        await self.db.predictions.create_index("order_id")
        await self.db.predictions.create_index("created_at")
        await self.db.predictions.create_index("prediction")

        await self.db.forecast_logs.create_index("created_at")
        await self.db.forecast_logs.create_index("category_name")


mongodb = MongoDB()


async def get_db() -> AsyncIOMotorDatabase | None:
    return mongodb.get_db()
