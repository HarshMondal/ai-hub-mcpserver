"""Application settings and configuration loading helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from pydantic import BaseModel, Field

from . import loaders


class ToolToggle(BaseModel):
    """Configuration fragment representing a tool's enablement state."""

    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class Settings(BaseModel):
    """Container for application configuration values."""

    app_name: str = Field(default="AI-Assistant Hub", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    enabled_tools: Dict[str, ToolToggle] = Field(default_factory=dict)
    config_file: Optional[Path] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = dict(populate_by_name=True, arbitrary_types_allowed=True)

    def tool_is_enabled(self, tool_name: str) -> bool:
        toggle = self.enabled_tools.get(tool_name, ToolToggle())
        return toggle.enabled

    def tool_config(self, tool_name: str) -> Dict[str, Any]:
        return self.enabled_tools.get(tool_name, ToolToggle()).config


def load_settings(*, config_path: Optional[Path] = None) -> Settings:
    """Load settings using environment variables and an optional config file."""

    merged: Dict[str, Any] = loaders.build_base_config()
    file_config = loaders.load_file_config(config_path or merged.get("CONFIG_FILE"))
    loaders.merge_dicts(merged, file_config)

    enabled_tools = _build_tool_toggles(loaders.extract_tool_configs(merged))
    extra = _extract_extra_fields(merged)

    return Settings(
        app_name=merged.get("APP_NAME", Settings.model_fields["app_name"].default),
        log_level=merged.get("LOG_LEVEL", Settings.model_fields["log_level"].default),
        enabled_tools=enabled_tools,
        config_file=_coerce_path(file_config.get("CONFIG_FILE")) if isinstance(file_config, Mapping) else None,
        extra=extra,
    )


def _build_tool_toggles(raw: Mapping[str, Mapping[str, Any]]) -> Dict[str, ToolToggle]:
    toggles: Dict[str, ToolToggle] = {}
    for name, config in raw.items():
        toggles[name] = ToolToggle(
            enabled=bool(config.get("enabled", True)),
            config=dict(config.get("config", {})),
        )
    return toggles


def _extract_extra_fields(config: Mapping[str, Any]) -> Dict[str, Any]:
    reserved = {"APP_NAME", "LOG_LEVEL", "CONFIG_FILE"}
    return {key: value for key, value in config.items() if key not in reserved and not key.startswith("TOOL_")}


def _coerce_path(value: Any) -> Optional[Path]:
    if value is None:
        return None
    return Path(str(value))


__all__ = ["Settings", "ToolToggle", "load_settings"]

