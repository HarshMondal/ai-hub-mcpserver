"""Weather tool registration."""
from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field

from ..integrations.weather import WeatherAdapter, WeatherConfig
from ..mcp.tooling import ToolSpec
from ..utils.errors import ToolExecutionError


class WeatherInput(BaseModel):
    location: str = Field(description="City name (e.g., 'London', 'New York')")
    units: str = Field(default="metric", description="Unit system: 'metric' (Celsius) or 'imperial' (Fahrenheit)")


class WeatherOutput(BaseModel):
    conditions: Dict[str, Optional[float | str | int]] = Field(default_factory=dict)


def build_tool(raw_config: Dict[str, object]) -> ToolSpec:
    """Create the weather tool spec using configuration from settings."""

    config = WeatherConfig.model_validate(raw_config)
    adapter = WeatherAdapter(config=config)

    async def handler(payload: WeatherInput, context: Optional[Dict[str, object]]) -> Dict[str, object]:
        units = payload.units.lower()
        if units not in {"metric", "imperial"}:
            raise ToolExecutionError("Invalid unit system. Choose 'metric' or 'imperial'.")

        conditions = await adapter.fetch_weather(location=payload.location, units=units)
        return {"conditions": conditions}

    description = "Retrieve current weather information for a specified city using OpenWeatherMap API."

    return ToolSpec(
        name="weather",
        description=description,
        input_model=WeatherInput,
        output_model=WeatherOutput,
        handler=handler,
    )


__all__ = ["build_tool", "WeatherInput", "WeatherOutput"]

