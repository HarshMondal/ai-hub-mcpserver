"""Helpers for building the settings context."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - optional dependency
    dotenv_values = None  # type: ignore


def build_base_config() -> Dict[str, Any]:
    """Return base configuration sourced from environment variables and `.env`."""

    base: Dict[str, Any] = {}
    env_file = Path(os.getenv("ENV_FILE", ".env"))
    if dotenv_values and env_file.exists():
        base.update(dotenv_values(str(env_file)))
    base.update(os.environ)
    normalized = {k.upper(): _coerce_value(v) for k, v in base.items() if v is not None}
    return normalized


def load_file_config(path: Any) -> Dict[str, Any]:
    """Load configuration from a JSON or YAML file if available."""

    if not path:
        return {}

    file_path = Path(str(path))
    if not file_path.exists():
        return {}

    text = file_path.read_text()
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError:  # pragma: no cover - optional dependency
            return {}
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        return {}

    data.setdefault("CONFIG_FILE", str(file_path))
    return {k.upper(): v for k, v in data.items()}


def merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    """Merge overrides into base dict recursively."""

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_dicts(base[key], value)  # type: ignore[index]
        else:
            base[key] = value


def extract_tool_configs(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract tool configuration from merged settings."""

    tools: Dict[str, Dict[str, Any]] = {}
    for key, value in config.items():
        if not key.startswith("TOOL_"):
            continue
        remainder = key[len("TOOL_") :]
        if remainder.endswith("_ENABLED"):
            tool_name = remainder[: -len("_ENABLED")].lower()
            entry = tools.setdefault(tool_name, {"enabled": True, "config": {}})
            entry["enabled"] = _coerce_bool(value)
        elif "_CONFIG__" in remainder:
            tool_name, config_key = remainder.split("_CONFIG__", 1)
            tool_entry = tools.setdefault(tool_name.lower(), {"enabled": True, "config": {}})
            tool_entry["config"][config_key.lower()] = value
        elif isinstance(value, dict):
            tool_entry = tools.setdefault(remainder.lower(), {"enabled": True, "config": {}})
            merge_dicts(tool_entry, value)
    return tools


def _coerce_value(value: Any) -> Any:
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return value


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


__all__ = [
    "build_base_config",
    "load_file_config",
    "merge_dicts",
    "extract_tool_configs",
]
