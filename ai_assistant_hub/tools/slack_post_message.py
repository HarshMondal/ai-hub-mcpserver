"""Slack post message tool registration."""
from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field

from ..integrations.slack import SlackAdapter, SlackConfig
from ..mcp.tooling import ToolSpec


class SlackPostMessageInput(BaseModel):
    channel: str = Field(description="Slack channel ID (C1234567890) or channel name (#general or general)")
    text: str = Field(description="Message text to post")
    thread_ts: Optional[str] = Field(default=None, description="Thread timestamp for replies (no validation)")


class SlackPostMessageOutput(BaseModel):
    message_ts: str = Field(description="Timestamp of posted message")
    status: str = Field(description="Status of message delivery")
    channel: str = Field(description="Channel ID where message was posted")
    channel_name: Optional[str] = Field(default=None, description="Channel name (if available)")
    permalink: Optional[str] = Field(default=None, description="Permalink to the message")


def build_tool(raw_config: Dict[str, object]) -> ToolSpec:
    """Create the Slack messaging tool specification."""

    config = SlackConfig.model_validate(raw_config)
    adapter = SlackAdapter(config=config)

    async def handler(payload: SlackPostMessageInput, context: Optional[Dict[str, object]]) -> Dict[str, object]:
        channel = payload.channel[1:] if payload.channel.startswith("#") else payload.channel
        result = await adapter.post_message(channel=channel, text=payload.text, thread_ts=payload.thread_ts)
        return result

    description = (
        "Post a message to a Slack channel. Supports channel IDs or channel names and optional threaded replies."
    )

    return ToolSpec(
        name="slack_post_message",
        description=description,
        input_model=SlackPostMessageInput,
        output_model=SlackPostMessageOutput,
        handler=handler,
    )


__all__ = ["build_tool", "SlackPostMessageInput", "SlackPostMessageOutput"]

