"""Logging helpers."""
from __future__ import annotations

import logging
from typing import Optional

from ..config.settings import Settings


def configure_logging(settings: Optional[Settings] = None) -> None:
    """Configure root logging using settings."""

    level = (settings.log_level if settings else "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


__all__ = ["configure_logging"]
