"""Tool discovery and registration utilities."""
from __future__ import annotations

import importlib
from typing import Callable, Dict

from ..config.settings import Settings
from ..mcp.tooling import ToolSpec
from ..utils.errors import ConfigurationError
from .mcp_server import AIHubMCPServer


ToolFactory = Callable[[Dict[str, object]], ToolSpec]


def load_tools(server: AIHubMCPServer, *, settings: Settings) -> None:
    """Load and register tools declared in the settings."""

    for tool_name, toggle in settings.enabled_tools.items():
        if not toggle.enabled:
            server.logger.debug("Tool %s disabled via configuration", tool_name)
            continue

        factory = _import_tool_factory(tool_name)
        spec = factory(toggle.config)
        server.register_tool(spec)


def _import_tool_factory(tool_name: str) -> ToolFactory:
    module_name = f"ai_assistant_hub.tools.{tool_name}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:  
        raise ConfigurationError(f"Tool module not found: {module_name}") from exc

    if not hasattr(module, "build_tool"):
        raise ConfigurationError(f"Tool module {module_name} missing build_tool")

    factory = getattr(module, "build_tool")
    if not callable(factory):
        raise ConfigurationError(f"Tool module {module_name} build_tool is not callable")
    return factory


__all__ = ["load_tools"]

