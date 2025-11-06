"""Async CLI entrypoint for running the AI Assistant Hub MCP server."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Awaitable, Callable, Dict

from ..config.settings import load_settings
from ..utils.logging import configure_logging
from .mcp_server import AIHubMCPServer
from .tool_loader import load_tools

TransportRunner = Callable[[object], Awaitable[None]]
DEFAULT_TRANSPORT = "stdio"
TRANSPORT_ENV_VAR = "AI_HUB_TRANSPORT"


async def create_mcp_server() -> tuple[AIHubMCPServer, object]:
    """Initialise the MCP server and return both the wrapper and underlying server."""

    settings = load_settings()
    configure_logging(settings)

    server = AIHubMCPServer(settings=settings)
    load_tools(server, settings=settings)
    server.log_startup()

    return server, server.mcp_server


def _available_transports() -> Dict[str, TransportRunner]:
    """Return the mapping of supported transport runners."""
    
    async def run_stdio(mcp_server: object) -> None:
        """Run MCP server with stdio transport."""
        if hasattr(mcp_server, 'run_stdio_async'):
            await mcp_server.run_stdio_async()
        else:
            raise RuntimeError("MCP server does not support stdio transport")
    
    transports: Dict[str, TransportRunner] = {"stdio": run_stdio}
    return transports


def _parse_args() -> argparse.Namespace:
    transports = _available_transports()
    parser = argparse.ArgumentParser(description="Run the AI Assistant Hub MCP server")
    parser.add_argument(
        "--transport",
        choices=sorted(transports.keys()),
        default=os.getenv(TRANSPORT_ENV_VAR, DEFAULT_TRANSPORT),
        help=(
            "Transport mechanism used to expose the MCP server. "
            f"Defaults to environment variable {TRANSPORT_ENV_VAR!r} or '{DEFAULT_TRANSPORT}'."
        ),
    )
    return parser.parse_args()


async def _run_cli(*, transport: str) -> None:
    try:
        _server_wrapper, mcp_server = await create_mcp_server()
        runner = _available_transports()[transport]

        logger = logging.getLogger("aihub.cli")
        logger.info("Starting MCP server with %s transport", transport)
        logger.info("Server ready, waiting for client connections...")
        # Also log to stderr so it's visible even when stdout is used for protocol
        print(f"MCP server started with {transport} transport. Waiting for client...", file=sys.stderr)
        print(f"Tools available: {[t.name for t in _server_wrapper.list_tools()]}", file=sys.stderr)

        try:
            await runner(mcp_server)
        except asyncio.CancelledError:  
            raise
        except KeyboardInterrupt:  
            logger.info("Received interrupt, shutting down transport")
        finally:
            logger.info("Transport %s stopped", transport)
    except Exception as e:
        
        logger = logging.getLogger("aihub.cli")
        logger.error("Failed to start MCP server: %s", e, exc_info=True)
        print(f"ERROR: Failed to start MCP server: {e}", file=sys.stderr)
        raise


def main() -> None:  
    args = _parse_args()
    try:
        asyncio.run(_run_cli(transport=args.transport))
    except KeyboardInterrupt:  
        logging.getLogger("aihub.cli").info("Interrupted before startup completed")


__all__ = [
    "create_mcp_server",
    "main",
]
if __name__ == "__main__":
    main()