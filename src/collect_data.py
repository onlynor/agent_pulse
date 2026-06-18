from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .config import (
        EMPTY_SOURCE_MESSAGE,
        GENERIC_ERROR_MESSAGE,
        ONLINE_FALLBACK_MESSAGE,
        REPOS_FILE,
        write_log,
    )
    from .data_store import (
        load_cache_dataframe,
        load_online_source_config,
        load_sample_records,
        save_dataset,
    )
    from .database import save_repositories
    from .github_client import GitHubClient
    from .transform import normalize_repositories
except ImportError:
    from config import (
        EMPTY_SOURCE_MESSAGE,
        GENERIC_ERROR_MESSAGE,
        ONLINE_FALLBACK_MESSAGE,
        REPOS_FILE,
        write_log,
    )
    from data_store import (
        load_cache_dataframe,
        load_online_source_config,
        load_sample_records,
        save_dataset,
    )
    from database import save_repositories
    from github_client import GitHubClient
    from transform import normalize_repositories


DEFAULT_REPOSITORIES = [
    "langchain-ai/langchain",
    "langchain-ai/langgraph",
    "crewAIInc/crewAI",
    "microsoft/autogen",
    "Significant-Gravitas/AutoGPT",
    "FoundationAgents/MetaGPT",
    "camel-ai/camel",
    "OpenBMB/ChatDev",
    "TransformerOptimus/SuperAGI",
    "e2b-dev/awesome-ai-agents",
    "openai/swarm",
    "agno-agi/agno",
    "openclaw/openclaw",
    "NousResearch/hermes-agent",
    "anomalyco/opencode",
]


def load_repo_list(path: Path = REPOS_FILE) -> list[str]:
    if not path.exists():
        return DEFAULT_REPOSITORIES.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        write_log("error", "repo_list_read_failed", type(exc).__name__)
        return []
    except json.JSONDecodeError as exc:
        write_log("error", "repo_list_json_invalid", type(exc).__name__)
        return []

    repos: list[str] = []
    for item in data:
        if isinstance(item, str):
            repos.append(item.strip())
        elif isinstance(item, dict):
            repos.append(str(item.get("full_name", "")).strip())
    return [repo for repo in repos if repo]


def refresh_repository_list() -> dict[str, Any]:
    try:
        repos = load_repo_list()
        if not repos:
            write_log("warning", "repo_list_empty", "no repositories configured")
            return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": []}

        client = GitHubClient()
        records: list[dict[str, Any]] = []
        errors: list[str] = []

        for repo in repos:
            result = client.get_repo(repo)
            if result.ok and result.data:
                records.append(result.data)
            else:
                errors.append(result.error)
                write_log("warning", "repo_collect_failed", f"{repo}: {result.error}")

        if not records:
            write_log("error", "collect_no_records", f"failed_count={len(errors)}")
            return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": errors}

        df = normalize_repositories(records)
        save_repositories(df)

        return {
            "ok": True,
            "message": "",
            "updated_count": len(df),
            "errors": errors,
        }
    except Exception as exc:
        write_log("error", "refresh_repository_data_failed", type(exc).__name__)
        return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": []}


def refresh_online_ecosystem() -> dict[str, Any]:
    try:
        config = load_online_source_config()
        client = GitHubClient()
        pinned_repos = [
            str(repo).strip()
            for repo in config.get("pinned_repositories", [])
            if str(repo).strip()
        ]
        pinned_records: list[dict[str, Any]] = []
        pinned_errors: list[str] = []

        for repo in pinned_repos:
            repo_result = client.get_repo(repo)
            if repo_result.ok and repo_result.data:
                pinned_records.append(repo_result.data)
            else:
                pinned_errors.append(f"{repo}: {repo_result.error}")
                write_log("warning", "pinned_repo_collect_failed", f"{repo}: {repo_result.error}")

        result = client.search_repositories(
            keywords=config.get("keywords") or [],
            topics=config.get("topics") or [],
            languages=config.get("languages") or [],
            min_stars=int(config.get("min_stars") or 0),
            pushed_after=str(config.get("pushed_after") or ""),
            max_repos=max(1, int(config.get("max_repos") or 300) - len(pinned_records)),
            sort=str(config.get("sort") or "stars"),
            order=str(config.get("order") or "desc"),
        )
        if not result.ok or not result.data:
            if pinned_records:
                df = save_dataset(pinned_records, active_source="在线开源生态数据", data_mode="online")
                save_repositories(df)
                return {
                    "ok": True,
                    "message": "",
                    "updated_count": len(df),
                    "data_mode": "online",
                    "errors": [*pinned_errors, result.error],
                }

            cached_df = load_cache_dataframe()
            if not cached_df.empty:
                save_repositories(cached_df)
                return {
                    "ok": True,
                    "message": ONLINE_FALLBACK_MESSAGE,
                    "updated_count": len(cached_df),
                    "data_mode": "cache",
                    "errors": [*pinned_errors, result.error],
                }
            return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": [*pinned_errors, result.error]}

        seen = set()
        records = []
        for record in [*pinned_records, *result.data.get("items", [])]:
            full_name = str(record.get("full_name", "")).strip()
            if full_name and full_name not in seen:
                seen.add(full_name)
                records.append(record)
        if not records:
            return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": []}

        df = save_dataset(records, active_source="在线开源生态数据", data_mode="online")
        save_repositories(df)
        return {
            "ok": True,
            "message": "",
            "updated_count": len(df),
            "data_mode": "online",
            "errors": pinned_errors,
        }
    except Exception as exc:
        write_log("error", "refresh_online_ecosystem_failed", type(exc).__name__)
        cached_df = load_cache_dataframe()
        if not cached_df.empty:
            save_repositories(cached_df)
            return {
                "ok": True,
                "message": ONLINE_FALLBACK_MESSAGE,
                "updated_count": len(cached_df),
                "data_mode": "cache",
                "errors": [],
            }
        return {"ok": False, "message": GENERIC_ERROR_MESSAGE, "errors": []}


def load_cache_source() -> dict[str, Any]:
    df = load_cache_dataframe()
    if df.empty:
        return {"ok": False, "message": EMPTY_SOURCE_MESSAGE, "errors": []}
    save_repositories(df)
    return {
        "ok": True,
        "message": "",
        "updated_count": len(df),
        "data_mode": "cache",
        "errors": [],
    }


def load_sample_source() -> dict[str, Any]:
    records = load_sample_records()
    if not records:
        return {"ok": False, "message": EMPTY_SOURCE_MESSAGE, "errors": []}
    df = save_dataset(records, active_source="示例数据集", data_mode="sample")
    save_repositories(df)
    return {
        "ok": True,
        "message": "",
        "updated_count": len(df),
        "data_mode": "sample",
        "errors": [],
    }


def update_data_source(source_label: str) -> dict[str, Any]:
    if source_label == "在线开源生态数据":
        return refresh_online_ecosystem()
    if source_label == "示例数据集":
        return load_sample_source()
    return load_cache_source()


def refresh_repository_data() -> dict[str, Any]:
    return refresh_repository_list()
