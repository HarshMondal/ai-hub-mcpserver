"""Slack integration adapter."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ..utils.auth import OAuthTokenAuth
from ..utils.errors import ToolExecutionError
from ..utils.http import ResilientAsyncHTTPClient


class SlackConfig(BaseModel):
    """Configuration values for Slack messaging integration."""

    token: str = Field(..., description="Slack bot token")
    token_type: str = Field(default="Bearer")
    base_url: str = Field(default="https://slack.com/api")
    timeout: float = Field(default=10.0)
    retries: int = Field(default=1)
    backoff_factor: float = Field(default=0.5)


class SlackAdapter:
    """Adapter responsible for Slack Web API communication."""

    def __init__(self, *, config: SlackConfig) -> None:
        headers: Dict[str, str] = {"Content-Type": "application/x-www-form-urlencoded"}
        headers.update(OAuthTokenAuth(token=config.token, token_type=config.token_type).headers())

        self.client = ResilientAsyncHTTPClient(
            base_url=config.base_url,
            timeout=config.timeout,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
            headers=headers,
        )

    async def post_message(
        self,
        *,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = await self.client.request("POST", "/chat.postMessage", data=payload)

        if not response.get("ok"):
            error_msg = response.get("error", "Unknown error")
            raise ToolExecutionError(f"Slack API error: {error_msg}")

        message_data = response.get("message", {})
        channel_data = response.get("channel", {})
        channel_id = channel_data if isinstance(channel_data, str) else channel_data.get("id", channel)
        channel_name = None
        if isinstance(channel_data, dict) and channel_data.get("name"):
            channel_name = f"#{channel_data['name']}"

        permalink = None
        message_ts = message_data.get("ts", "")
        if message_ts and channel_id:
            permalink = f"https://slack.com/archives/{channel_id}/p{message_ts.replace('.', '')}"

        return {
            "message_ts": message_ts,
            "status": "sent",
            "channel": channel_id,
            "channel_name": channel_name,
            "permalink": permalink,
        }


__all__ = ["SlackAdapter", "SlackConfig"]

