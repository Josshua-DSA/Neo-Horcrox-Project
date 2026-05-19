"""Application health routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..core.database import mongodb
from ..core.model_registry import model_registry

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Backend health check")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "models": model_registry.status(),
        "mongodb": mongodb.status(),
    }
