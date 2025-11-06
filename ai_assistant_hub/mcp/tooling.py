"""Utilities for registering tools with the official MCP server."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel

from ..schemas.base import ToolInvocationRequest, ToolInvocationResponse
from ..utils.errors import ToolExecutionError

try:  # pragma: no cover - optional dependency runtime check
    from mcp import types as mcp_types  # type: ignore
except Exception:  # pragma: no cover - handled gracefully at runtime
    mcp_types = None  # type: ignore


ToolHandler = Callable[[BaseModel, Optional[Any]], Awaitable[Any]]


@dataclass
class ToolSpec:
    """In-memory representation of an MCP tool."""

    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: ToolHandler

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
        }

    def bind_to_server(self, server: Any) -> None:
        """Register the tool with the official MCP server instance."""

        if mcp_types is None:
            raise RuntimeError("The 'mcp' package is required but not installed")

        async def mcp_handler(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            arguments, context = _extract_invocation_payload(args, kwargs)
            payload = self.input_model.model_validate(arguments)
            context_payload = context if isinstance(context, dict) else None
            result = await self.handler(payload, context_payload)
            if isinstance(result, BaseModel):
                return result.model_dump()
            return self.output_model.model_validate(result).model_dump()

        input_schema = self.input_model.model_json_schema()
        output_schema = self.output_model.model_json_schema()

        add_tool = getattr(server, "add_tool", None)
        if callable(add_tool):
            try:
                # FastMCP (mcp >= 1.20.0) expects function as first arg
                # Use Pydantic model as type annotation so FastMCP can infer schema
                input_model_cls = self.input_model
                output_model_cls = self.output_model
                
                async def fastmcp_handler(input_data: Any) -> Any:  # type: ignore
                    """Wrapper for FastMCP tool registration."""
                    # Validate input using the Pydantic model
                    validated_input = input_model_cls.model_validate(input_data)
                    result = await self.handler(validated_input, None)
                    if isinstance(result, BaseModel):
                        return result  # type: ignore
                    return output_model_cls.model_validate(result)
                
                # Set type annotations dynamically for FastMCP schema inference
                fastmcp_handler.__annotations__ = {
                    'input_data': input_model_cls,
                    'return': output_model_cls,
                }
                
                # Try FastMCP API (function as first argument)
                add_tool(
                    fastmcp_handler,
                    name=self.name,
                    description=self.description,
                )
                return
            except TypeError:
                # Fallback: try old API with keyword arguments
                try:
                    add_tool(
                        name=self.name,
                        description=self.description,
                        input_schema=input_schema,
                        output_schema=output_schema,
                        handler=mcp_handler,
                    )
                    return
                except (TypeError, Exception):
                    pass
            except Exception:  # pragma: no cover - compatibility shim
                if mcp_types is not None:
                    tool_cls = getattr(mcp_types, "Tool", None) or getattr(
                        mcp_types, "ToolDefinition", None
                    )
                    if tool_cls is not None:
                        try:
                            tool_obj = tool_cls(
                                name=self.name,
                                description=self.description,
                                input_schema=input_schema,
                                output_schema=output_schema,
                            )
                            add_tool(tool_obj, mcp_handler)
                            return
                        except Exception:
                            pass

        register_tool = getattr(server, "register_tool", None)
        if callable(register_tool):
            try:
                register_tool(
                    name=self.name,
                    description=self.description,
                    input_schema=input_schema,
                    output_schema=output_schema,
                    handler=mcp_handler,
                )
                return
            except Exception:
                pass

        tool_decorator = getattr(server, "tool", None)
        if callable(tool_decorator):
            decorated = tool_decorator(
                name=self.name,
                description=self.description,
                input_schema=input_schema,
                output_schema=output_schema,
            )
            decorated(mcp_handler)
            return

        raise RuntimeError("Incompatible MCP server: missing tool registration API")

    async def invoke(self, request: ToolInvocationRequest) -> ToolInvocationResponse:
        payload = self.input_model.model_validate(request.input or {})
        try:
            raw_output = await self.handler(payload, request.context)
        except ToolExecutionError as exc:
            return ToolInvocationResponse(ok=False, output={}, error=str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            raise ToolExecutionError(str(exc)) from exc

        if isinstance(raw_output, BaseModel):
            output_model = raw_output
        else:
            output_model = self.output_model.model_validate(raw_output)

        return ToolInvocationResponse(ok=True, output=output_model.model_dump())


def _extract_invocation_payload(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Any]]:
    """Normalize invocation payloads from the official MCP server."""

    context: Optional[Any] = None
    arguments: Optional[Dict[str, Any]] = None

    if "arguments" in kwargs:
        arguments = kwargs.get("arguments")
    elif "input" in kwargs:
        arguments = kwargs.get("input")
    elif "params" in kwargs:
        arguments = kwargs.get("params")

    if "context" in kwargs:
        context = kwargs.get("context")

    if arguments is None and args:
        if isinstance(args[0], dict):
            arguments = args[0]
            if len(args) > 1:
                context = args[1]
        else:
            context = args[0]
            if len(args) > 1:
                candidate = args[1]
                if isinstance(candidate, dict):
                    arguments = candidate
                elif hasattr(candidate, "model_dump"):
                    arguments = candidate.model_dump()
                else:
                    arguments = candidate

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict) and hasattr(arguments, "model_dump"):
        arguments = arguments.model_dump()
    elif not isinstance(arguments, dict):
        try:
            arguments = dict(arguments)  # type: ignore[arg-type]
        except Exception:  # pragma: no cover - defensive casting
            arguments = {"value": arguments}

    return arguments, context


@dataclass
class ToolCatalog:
    """Holds registered tool specifications for local invocation and metadata."""

    tools: Dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self.tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self.tools[spec.name] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self.tools.get(name)

    def list(self) -> List[ToolSpec]:
        return list(self.tools.values())


__all__ = ["ToolSpec", "ToolCatalog"]

