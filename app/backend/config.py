"""Backward-compatible settings import.

New backend code should import from backend.core.config.
"""

from .core.config import Settings, settings

__all__ = ["Settings", "settings"]
