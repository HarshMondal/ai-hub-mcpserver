"""Custom exception types and helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..schemas.base import ErrorDetail


class AIHubError(Exception):
    """Base exception for the AI Assistant Hub."""


class ConfigurationError(AIHubError):
    """Raised when configuration issues are detected."""


class ToolExecutionError(AIHubError):
    """Raised when tool execution fails."""


@dataclass
class ToolErrorPayload:
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_error_detail(self) -> ErrorDetail:
        return ErrorDetail(message=self.message, code=self.code, details=self.details)


__all__ = [
    "AIHubError",
    "ConfigurationError",
    "ToolExecutionError",
    "ToolErrorPayload",
]
