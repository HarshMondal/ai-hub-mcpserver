"""Integration adapters used by MCP tools."""

from .weather import WeatherAdapter, WeatherConfig
from .github import GitHubIssuesAdapter, GitHubIssuesConfig
from .slack import SlackAdapter, SlackConfig

__all__ = [
    "WeatherAdapter",
    "WeatherConfig",
    "GitHubIssuesAdapter",
    "GitHubIssuesConfig",
    "SlackAdapter",
    "SlackConfig",
]

