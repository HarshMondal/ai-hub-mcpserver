"""Server abstraction for handling MCP interactions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency runtime check
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore
    except ImportError:
        from mcp.server import Server as MCPServer  # type: ignore
    try:
        from mcp.server import ServerOptions as MCPServerOptions  # type: ignore
    except ImportError:  
        MCPServerOptions = None  # type: ignore
except Exception:  
    MCPServer = None  # type: ignore
    MCPServerOptions = None  # type: ignore

from ..config.settings import Settings
from ..mcp.tooling import ToolCatalog, ToolSpec
from ..schemas.base import ToolInvocationRequest, ToolInvocationResponse
from ..utils.errors import ToolExecutionError


@dataclass
class AIHubMCPServer:
    """Thin wrapper around the official MCP server."""

    settings: Settings
    mcp_server: Any = field(init=False)
    catalog: ToolCatalog = field(default_factory=ToolCatalog)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("aihub.mcp"))

    def __post_init__(self) -> None:
        if MCPServer is None:  
            raise RuntimeError(
                "The 'mcp' package is required to run the MCP server."
            )

        server: Optional[Any] = None
        if MCPServerOptions is not None:
            try:
                options = MCPServerOptions(name=self.settings.app_name)
                server = MCPServer(options)
            except Exception:  
                server = None

        if server is None:
            try:
                server = MCPServer(name=self.settings.app_name)
            except TypeError:
                server = MCPServer(self.settings.app_name)

        self.mcp_server = server

    def register_tool(self, spec: ToolSpec) -> None:
        self.catalog.register(spec)
        spec.bind_to_server(self.mcp_server)
        self.logger.debug("Registered MCP tool %s", spec.name)

    async def invoke(self, request: ToolInvocationRequest) -> ToolInvocationResponse:
        spec = self.catalog.get(request.tool)
        if not spec:
            raise ToolExecutionError(f"Unknown tool: {request.tool}")
        return await spec.invoke(request)

    def list_tools(self) -> List[ToolSpec]:
        return self.catalog.list()

    def metadata(self) -> Dict[str, Any]:
        name = getattr(self.mcp_server, "name", self.settings.app_name)
        return {"app_name": name, "tool_count": len(self.catalog.tools)}

    def log_startup(self) -> None:
        meta = self.metadata()
        self.logger.info(
            "Starting %s with %s registered tools",
            meta["app_name"],
            meta["tool_count"],
        )


__all__ = ["AIHubMCPServer"]

