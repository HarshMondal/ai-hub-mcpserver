"""Weather integration adapter."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from ..utils.errors import ToolExecutionError
from ..utils.http import ResilientAsyncHTTPClient


class WeatherConfig(BaseModel):
    """Configuration required for the weather integration."""

    api_key: str = Field(..., description="OpenWeatherMap API key")
    base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="Base URL for the weather API",
    )
    timeout: float = Field(default=10.0, description="Request timeout in seconds")
    retries: int = Field(default=1, description="Number of retry attempts for failed requests")
    backoff_factor: float = Field(default=0.5, description="Retry backoff factor")


class WeatherAdapter:
    """Adapter that encapsulates OpenWeatherMap API interaction."""

    def __init__(self, *, config: WeatherConfig) -> None:
        self.config = config
        self.client = ResilientAsyncHTTPClient(
            base_url=config.base_url,
            timeout=config.timeout,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
        )

    async def fetch_weather(self, *, location: str, units: str) -> Dict[str, Any]:
        if not self.config.api_key:
            raise ToolExecutionError("Weather API key not configured. Set TOOL_WEATHER_CONFIG__API_KEY")

        params = {
            "q": location,
            "units": units,
            "appid": self.config.api_key,
        }

        response = await self.client.request("GET", "/weather", params=params)

        main = response.get("main", {})
        weather = response.get("weather", [{}])[0]
        wind = response.get("wind", {})
        location_name = response.get("name", location)
        country = response.get("sys", {}).get("country", "")
        location_str = f"{location_name}, {country}" if country else location_name

        return {
            "location": location_str,
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "description": weather.get("description", ""),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "visibility": response.get("visibility"),
            "clouds": response.get("clouds", {}).get("all"),
            "units": units,
        }


__all__ = ["WeatherAdapter", "WeatherConfig"]

