from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

try:
    from .config import load_settings, write_log
except ImportError:
    from config import load_settings, write_log


@dataclass
class GitHubResponse:
    ok: bool
    data: dict[str, Any] | None = None
    error: str = ""
    log_message: str = ""
    remaining: str | None = None


class GitHubClient:
    def __init__(self) -> None:
        settings = load_settings()
        self.base_url = settings["github_api_base_url"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "AgentPulse",
            }
        )
        if settings["github_token"]:
            self.session.headers.update(
                {"Authorization": f"Bearer {settings['github_token']}"}
            )

    def _request_json(self, path: str, *, params: dict[str, Any] | None = None, log_key: str = "") -> GitHubResponse:
        try:
            response = self.session.get(f"{self.base_url}{path}", params=params, timeout=20)
        except requests.Timeout:
            write_log("warning", "github_timeout", log_key)
            return GitHubResponse(False, error="网络请求超时")
        except requests.RequestException as exc:
            write_log("warning", "github_network_error", f"{log_key}: {type(exc).__name__}")
            return GitHubResponse(False, error="网络请求失败")

        remaining = response.headers.get("X-RateLimit-Remaining")
        if response.status_code in {403, 429} and remaining == "0":
            write_log("warning", "github_rate_limit", log_key)
            return GitHubResponse(
                False,
                error="GitHub 访问频率受限",
                remaining=remaining,
            )

        if response.status_code == 404:
            write_log("warning", "github_repo_not_found", log_key)
            return GitHubResponse(
                False,
                error="仓库不存在或无访问权限",
                remaining=remaining,
            )

        if not response.ok:
            write_log(
                "warning",
                "github_http_error",
                f"{log_key}: status={response.status_code}",
            )
            return GitHubResponse(
                False,
                error="GitHub 数据请求失败",
                remaining=remaining,
            )

        try:
            data = response.json()
        except ValueError:
            write_log("warning", "github_invalid_json", log_key)
            return GitHubResponse(False, error="GitHub 返回数据异常")

        if not data:
            write_log("warning", "github_empty_data", log_key)
            return GitHubResponse(False, error="GitHub 返回空数据")

        return GitHubResponse(True, data=data, remaining=remaining)

    def get_repo(self, full_name: str) -> GitHubResponse:
        if "/" not in full_name:
            write_log("warning", "invalid_repo_name", full_name)
            return GitHubResponse(False, error="仓库名称格式无效")

        return self._request_json(f"/repos/{full_name}", log_key=full_name)

    def search_repositories(
        self,
        *,
        keywords: list[str] | None = None,
        topics: list[str] | None = None,
        languages: list[str] | None = None,
        min_stars: int = 1000,
        pushed_after: str = "",
        max_repos: int = 300,
        sort: str = "stars",
        order: str = "desc",
    ) -> GitHubResponse:
        common_parts: list[str] = []
        for language in languages or []:
            if language:
                common_parts.append(f"language:{language}")
        if min_stars > 0:
            common_parts.append(f"stars:>={int(min_stars)}")
        if pushed_after:
            common_parts.append(f"pushed:>={pushed_after}")

        queries: list[str] = []
        for topic in topics or []:
            if topic:
                queries.append(" ".join([f"topic:{topic}", *common_parts]).strip())
        for keyword in keywords or ["agent", "agentic"]:
            if keyword:
                queries.append(" ".join([str(keyword), *common_parts]).strip())
        if not queries:
            queries = [" ".join(["agent", *common_parts]).strip()]

        collected: list[dict[str, Any]] = []
        seen: set[str] = set()
        per_page = 100
        max_pages = max(1, min(10, (max_repos + per_page - 1) // per_page))
        remaining: str | None = None

        for query_index, query in enumerate(queries, start=1):
            for page in range(1, max_pages + 1):
                result = self._request_json(
                    "/search/repositories",
                    params={
                        "q": query,
                        "sort": sort,
                        "order": order,
                        "per_page": per_page,
                        "page": page,
                    },
                    log_key=f"search_{query_index}_page_{page}",
                )
                remaining = result.remaining
                if not result.ok or not result.data:
                    if collected:
                        break
                    continue

                items = result.data.get("items", [])
                if not items:
                    break

                for item in items:
                    full_name = str(item.get("full_name", "")).strip()
                    if full_name and full_name not in seen:
                        seen.add(full_name)
                        collected.append(item)
                    if len(collected) >= max_repos:
                        break
                if len(collected) >= max_repos:
                    break
            if len(collected) >= max_repos:
                break

        if not collected:
            return GitHubResponse(False, error="GitHub 返回空数据", remaining=remaining)
        return GitHubResponse(True, data={"items": collected}, remaining=remaining)
