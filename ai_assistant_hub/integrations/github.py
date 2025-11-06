"""GitHub integration adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..utils.auth import OAuthTokenAuth
from ..utils.errors import ToolExecutionError
from ..utils.http import ResilientAsyncHTTPClient


class GitHubIssuesConfig(BaseModel):
    """Configuration values for the GitHub issues integration."""

    base_url: str = Field(default="https://api.github.com")
    token: Optional[str] = Field(default=None)
    token_type: str = Field(default="Bearer")
    timeout: float = Field(default=10.0)
    retries: int = Field(default=1)
    backoff_factor: float = Field(default=0.5)


class GitHubIssuesAdapter:
    """Adapter responsible for communicating with the GitHub REST API."""

    def __init__(self, *, config: GitHubIssuesConfig) -> None:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        if config.token:
            headers.update(OAuthTokenAuth(token=config.token, token_type=config.token_type).headers())

        self.client = ResilientAsyncHTTPClient(
            base_url=config.base_url,
            timeout=config.timeout,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
            headers=headers,
        )

    async def ensure_repository(self, owner: str, repo: str) -> None:
        try:
            await self.client.request("GET", f"/repos/{owner}/{repo}")
        except ToolExecutionError as exc:
            message = str(exc)
            if "404" in message or "Not Found" in message:
                raise ToolExecutionError(
                    f"Repository '{owner}/{repo}' not found. Confirm owner and repository name."
                ) from exc
            if "403" in message or "Forbidden" in message:
                raise ToolExecutionError(
                    f"Repository '{owner}/{repo}' is private or inaccessible. Provide a GitHub token via TOOL_GITHUB_ISSUES_CONFIG__TOKEN"
                ) from exc
            raise

    async def list_issues(
        self,
        *,
        owner: str,
        repo: str,
        state: str,
        labels: Optional[List[str]],
        page: int,
        per_page: int,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "state": state,
            "page": page,
            "per_page": min(per_page, 100),
        }
        if labels:
            params["labels"] = ",".join(labels)

        issues_response = await self.client.request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params=params,
        )

        issues: List[Dict[str, Any]] = []
        for issue in issues_response:
            if "pull_request" in issue:
                continue
            issues.append(
                {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "state": issue.get("state"),
                    "url": issue.get("html_url"),
                    "body": (issue.get("body", "") or "")[:500],
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "labels": [label.get("name") for label in issue.get("labels", [])],
                    "user": issue.get("user", {}).get("login"),
                    "assignees": [assignee.get("login") for assignee in issue.get("assignees", [])],
                }
            )
        return issues


__all__ = ["GitHubIssuesAdapter", "GitHubIssuesConfig"]

