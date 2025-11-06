"""HTTP client helpers."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from .errors import ToolExecutionError

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency
    httpx = None  # type: ignore

logger = logging.getLogger("aihub.http")


class ResilientAsyncHTTPClient:
    """Async HTTP client with retry and timeout management."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
        backoff_factor: float = 0.5,
    ) -> None:
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout
        self.retries = max(retries, 0)
        self.backoff_factor = max(backoff_factor, 0)

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        if httpx is None:  # pragma: no cover - optional dependency
            raise RuntimeError("httpx is required for HTTP operations")

        attempt = 0
        last_error: Optional[Exception] = None
        while attempt <= self.retries:
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    headers=self.headers,
                    timeout=self.timeout,
                ) as session:
                    response = await session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as exc:
                error_detail = _extract_error_detail(exc)
                raise ToolExecutionError(
                    f"API request failed: {exc.response.status_code} {exc.response.reason_phrase}. "
                    f"Details: {error_detail}"
                ) from exc
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt == self.retries:
                    break
                sleep_for = self.backoff_factor * (2**attempt)
                logger.debug(
                    "HTTP request error (attempt %s/%s): %s. Retrying in %.2fs",
                    attempt + 1,
                    self.retries + 1,
                    exc,
                    sleep_for,
                )
                attempt += 1
                if sleep_for:
                    await asyncio.sleep(sleep_for)
            except Exception as exc:  # pragma: no cover - safety net
                raise ToolExecutionError(f"Unexpected HTTP error: {exc}") from exc

        raise ToolExecutionError(f"Request failed after {self.retries + 1} attempts: {last_error}")


def _extract_error_detail(exc: "httpx.HTTPStatusError") -> str:
    detail = str(exc)
    try:
        if exc.response.text:
            detail = exc.response.text
    except Exception:  # pragma: no cover - defensive
        pass
    return detail


__all__ = ["ResilientAsyncHTTPClient"]
