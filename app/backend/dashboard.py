"""Compatibility entrypoint for dashboard backend helpers."""

from __future__ import annotations

from .routes.dashboard_routes import router
from .services.dashboard_service import dashboard_service

__all__ = ["router", "dashboard_service"]
