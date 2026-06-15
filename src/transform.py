from __future__ import annotations

from typing import Any

import pandas as pd

try:
    from .classifier import add_categories
    from .scoring import add_scores
except ImportError:
    from classifier import add_categories
    from scoring import add_scores


REPOSITORY_COLUMNS = [
    "id",
    "full_name",
    "name",
    "owner",
    "description",
    "html_url",
    "homepage",
    "language",
    "topics",
    "license",
    "stargazers_count",
    "forks_count",
    "watchers_count",
    "subscribers_count",
    "open_issues_count",
    "size",
    "created_at",
    "updated_at",
    "pushed_at",
    "archived",
    "disabled",
    "default_branch",
    "release_count",
    "latest_release_at",
    "recent_commit_count_30d",
    "recent_commit_count_90d",
    "open_pr_count",
    "closed_pr_count",
    "contributor_count",
    "issue_close_rate",
    "avg_issue_close_days",
    "category",
    "stars_per_day",
    "fork_star_ratio",
    "issue_star_ratio",
    "activity_score",
    "growth_score",
    "maintenance_pressure",
    "health_score",
    "ecosystem_score",
    "recency_score",
    "community_score",
    "influence_score",
]


def _owner_name(owner: object) -> str:
    if isinstance(owner, dict):
        return str(owner.get("login", ""))
    return str(owner or "")


def _license_name(license_info: object) -> str:
    if isinstance(license_info, dict):
        return str(license_info.get("spdx_id") or license_info.get("key") or "Unknown")
    return str(license_info or "Unknown")


def _topics_text(topics: object) -> str:
    if isinstance(topics, list):
        return ", ".join(str(topic) for topic in topics if topic)
    return str(topics or "")


def normalize_repositories(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=REPOSITORY_COLUMNS)

    rows = []
    for item in records:
        full_name = item.get("full_name", "")
        owner = _owner_name(item.get("owner")) or str(full_name).split("/")[0]
        rows.append(
            {
                "id": item.get("id"),
                "full_name": full_name,
                "name": item.get("name", ""),
                "owner": owner,
                "description": item.get("description") or "",
                "html_url": item.get("html_url", ""),
                "homepage": item.get("homepage") or "",
                "language": item.get("language") or "Unknown",
                "topics": _topics_text(item.get("topics")),
                "license": _license_name(item.get("license")),
                "stargazers_count": item.get("stargazers_count") or 0,
                "forks_count": item.get("forks_count") or 0,
                "watchers_count": item.get("watchers_count") or 0,
                "subscribers_count": item.get("subscribers_count") or 0,
                "open_issues_count": item.get("open_issues_count") or 0,
                "size": item.get("size") or 0,
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
                "pushed_at": item.get("pushed_at", ""),
                "archived": bool(item.get("archived", False)),
                "disabled": bool(item.get("disabled", False)),
                "default_branch": item.get("default_branch") or "",
                "release_count": item.get("release_count") or 0,
                "latest_release_at": item.get("latest_release_at") or "",
                "recent_commit_count_30d": item.get("recent_commit_count_30d") or 0,
                "recent_commit_count_90d": item.get("recent_commit_count_90d") or 0,
                "open_pr_count": item.get("open_pr_count") or 0,
                "closed_pr_count": item.get("closed_pr_count") or 0,
                "contributor_count": item.get("contributor_count") or 0,
                "issue_close_rate": item.get("issue_close_rate") or 0,
                "avg_issue_close_days": item.get("avg_issue_close_days") or 0,
            }
        )

    df = pd.DataFrame(rows)
    numeric_columns = [
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "watchers_count",
        "subscribers_count",
        "size",
        "release_count",
        "recent_commit_count_30d",
        "recent_commit_count_90d",
        "open_pr_count",
        "closed_pr_count",
        "contributor_count",
        "issue_close_rate",
        "avg_issue_close_days",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    df = add_categories(df)
    df = add_scores(df)
    for column in REPOSITORY_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[REPOSITORY_COLUMNS]
