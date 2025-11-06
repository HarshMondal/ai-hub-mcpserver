"""Authentication helpers and placeholders."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class AuthStrategy(ABC):
    """Base class for authentication strategies."""

    @abstractmethod
    def headers(self) -> Dict[str, str]:
        """Return HTTP headers containing authentication information."""


class APIKeyAuth(AuthStrategy):
    """Simple API key authentication."""

    def __init__(self, header_name: str, api_key: str) -> None:
        self.header_name = header_name
        self.api_key = api_key

    def headers(self) -> Dict[str, str]:
        return {self.header_name: self.api_key}


class OAuthTokenAuth(AuthStrategy):
    """Placeholder OAuth token strategy with TODO for refresh logic."""

    def __init__(self, token: str, token_type: str = "Bearer") -> None:
        self.token = token
        self.token_type = token_type

    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"{self.token_type} {self.token}"}


__all__ = ["AuthStrategy", "APIKeyAuth", "OAuthTokenAuth"]
