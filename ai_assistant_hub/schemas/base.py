"""Shared schema definitions for tool interactions."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """Basic metadata describing a tool."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class ToolInvocationRequest(BaseModel):
    """Schema for invoking a tool."""

    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = None


class ToolInvocationResponse(BaseModel):
    """Schema representing a tool's response payload."""

    ok: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ErrorDetail(BaseModel):
    """Structured error information for clients."""

    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


__all__ = [
    "ToolMetadata",
    "ToolInvocationRequest",
    "ToolInvocationResponse",
    "ErrorDetail",
]
