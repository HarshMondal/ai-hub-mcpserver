"""GitHub issues tool registration."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ..integrations.github import GitHubIssuesAdapter, GitHubIssuesConfig
from ..mcp.tooling import ToolSpec
from ..utils.errors import ToolExecutionError


class GitHubIssuesInput(BaseModel):
    owner: str = Field(description="GitHub organization or user")
    repo: str = Field(description="Repository name")
    state: Optional[str] = Field(default="open", description="Issue state filter: 'open', 'closed', or 'all'")
    labels: Optional[List[str]] = Field(default=None, description="Filter issues by labels (list of label names)")
    page: Optional[int] = Field(default=1, description="Page number for pagination (starts at 1)")
    per_page: Optional[int] = Field(default=30, description="Number of issues per page (max 100)")


class GitHubIssuesOutput(BaseModel):
    issues: List[Dict[str, object]] = Field(default_factory=list)
    repository_exists: bool = Field(default=True)
    total_count: Optional[int] = Field(default=None, description="Total number of issues (if available)")


def build_tool(raw_config: Dict[str, object]) -> ToolSpec:
    """Create the GitHub issues tool specification."""

    config = GitHubIssuesConfig.model_validate(raw_config)
    adapter = GitHubIssuesAdapter(config=config)

    async def handler(payload: GitHubIssuesInput, context: Optional[Dict[str, object]]) -> Dict[str, object]:
        state = (payload.state or "open").lower()
        if state not in {"open", "closed", "all"}:
            raise ToolExecutionError("Invalid issue state. Choose 'open', 'closed', or 'all'.")

        await adapter.ensure_repository(payload.owner, payload.repo)
        issues = await adapter.list_issues(
            owner=payload.owner,
            repo=payload.repo,
            state=state,
            labels=payload.labels,
            page=payload.page or 1,
            per_page=payload.per_page or 30,
        )

        return {
            "issues": issues,
            "repository_exists": True,
            "total_count": len(issues),
        }

    description = (
        "List and summarize GitHub issues for a repository. "
        "Validates repository existence before fetching issues. "
        "Supports filtering by state and labels, with pagination."
    )

    return ToolSpec(
        name="github_issues",
        description=description,
        input_model=GitHubIssuesInput,
        output_model=GitHubIssuesOutput,
        handler=handler,
    )


__all__ = ["build_tool", "GitHubIssuesInput", "GitHubIssuesOutput"]

