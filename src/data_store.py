from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .config import (
        DEFAULT_CACHE_TTL_HOURS,
        DEFAULT_MAX_REPOS,
        DERIVED_DIR,
        MANIFEST_FILE,
        ONLINE_SOURCE_FILE,
        RAW_REPOS_DIR,
        REPOS_FILE,
        SAMPLE_SOURCE_FILE,
        SEED_DATA_FILE,
        SNAPSHOTS_DIR,
        ensure_data_directories,
        write_log,
    )
    from .csv_store import load_repos_from_csv, save_repos_to_csv, RAW_REPOS_CSV
    from .insights import generate_insights
    from .transform import REPOSITORY_COLUMNS, normalize_repositories
except ImportError:
    from config import (
        DEFAULT_CACHE_TTL_HOURS,
        DEFAULT_MAX_REPOS,
        DERIVED_DIR,
        MANIFEST_FILE,
        ONLINE_SOURCE_FILE,
        RAW_REPOS_DIR,
        REPOS_FILE,
        SAMPLE_SOURCE_FILE,
        SEED_DATA_FILE,
        SNAPSHOTS_DIR,
        ensure_data_directories,
        write_log,
    )
    from csv_store import load_repos_from_csv, save_repos_to_csv, RAW_REPOS_CSV
    from insights import generate_insights
    from transform import REPOSITORY_COLUMNS, normalize_repositories


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_file_name(full_name: str) -> str:
    safe_name = full_name.replace("/", "__").replace("\\", "__").strip()
    return f"{safe_name}.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        write_log("error", "json_read_failed", f"{path.name}: {type(exc).__name__}")
        return default


def write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        write_log("error", "json_write_failed", f"{path.name}: {type(exc).__name__}")


def default_online_source() -> dict[str, Any]:
    return {
        "name": "在线开源生态数据",
        "keywords": ["agent", "agentic", "ai agents"],
        "topics": ["ai-agent", "ai-agents", "agentic-ai", "autonomous-agents"],
        "languages": [],
        "min_stars": 1000,
        "pushed_after": "",
        "max_repos": DEFAULT_MAX_REPOS,
        "sort": "stars",
        "order": "desc",
    }


def ensure_source_files() -> None:
    ensure_data_directories()
    if not ONLINE_SOURCE_FILE.exists():
        write_json(ONLINE_SOURCE_FILE, default_online_source())
    if not SAMPLE_SOURCE_FILE.exists():
        repos = read_json(REPOS_FILE, [])
        write_json(
            SAMPLE_SOURCE_FILE,
            {
                "name": "示例数据集",
                "repositories": repos,
            },
        )


def read_manifest() -> dict[str, Any]:
    manifest = read_json(MANIFEST_FILE, {})
    if manifest:
        return manifest
    return {
        "version": "v2",
        "schema_version": "2.0",
        "last_updated_at": "",
        "active_source": "本地缓存数据",
        "repo_count": 0,
        "data_mode": "cache",
        "cache_ttl_hours": DEFAULT_CACHE_TTL_HOURS,
    }


def write_manifest(
    *,
    active_source: str,
    repo_count: int,
    data_mode: str,
    last_updated_at: str | None = None,
) -> None:
    write_json(
        MANIFEST_FILE,
        {
            "version": "v2",
            "schema_version": "2.0",
            "last_updated_at": last_updated_at or utc_now(),
            "active_source": active_source,
            "repo_count": int(repo_count),
            "data_mode": data_mode,
            "cache_ttl_hours": DEFAULT_CACHE_TTL_HOURS,
        },
    )


def load_legacy_seed_records() -> list[dict[str, Any]]:
    records = read_json(SEED_DATA_FILE, [])
    if isinstance(records, list):
        return [record for record in records if isinstance(record, dict)]
    return []


def save_raw_repo_records(records: list[dict[str, Any]]) -> None:
    ensure_data_directories()

    # 保存到 CSV（主存储）
    save_repos_to_csv(records)


def load_raw_repo_records() -> list[dict[str, Any]]:
    ensure_data_directories()

    # 优先从 CSV 加载
    if RAW_REPOS_CSV.exists():
        records = load_repos_from_csv()
        if records:
            write_log("info", "loaded_from_csv", f"{len(records)} records")
            return records

    # CSV 不存在时，回退到可选的旧 JSON 文件
    write_log("info", "fallback_to_json", "CSV not found, loading from legacy JSON files")
    records: list[dict[str, Any]] = []
    for path in sorted(RAW_REPOS_DIR.glob("*.json")):
        record = read_json(path, {})
        if isinstance(record, dict) and record.get("full_name"):
            records.append(record)

    # 如果从 JSON 加载成功，则保存为 CSV 方便下次读取
    if records:
        save_repos_to_csv(records)
        write_log("info", "auto_migrate_csv", f"saved {len(records)} records to CSV")

    return records


def write_snapshot(df: pd.DataFrame, data_mode: str) -> None:
    if df.empty:
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot = {
        "snapshot_date": today,
        "data_mode": data_mode,
        "repo_count": int(len(df)),
        "total_stars": int(df["stargazers_count"].sum()),
        "total_forks": int(df["forks_count"].sum()),
        "total_open_issues": int(df["open_issues_count"].sum()),
        "repositories": df["full_name"].tolist(),
    }
    write_json(SNAPSHOTS_DIR / f"{today}.json", snapshot)


def write_derived_files(df: pd.DataFrame) -> None:
    ensure_data_directories()
    if df.empty:
        return

    metrics_columns = [
        "full_name",
        "category",
        "language",
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "influence_score",
        "activity_score",
        "growth_score",
        "maintenance_pressure",
        "health_score",
        "ecosystem_score",
    ]
    write_json(DERIVED_DIR / "repos_metrics.json", df[metrics_columns].to_dict("records"))
    write_json(
        DERIVED_DIR / "language_distribution.json",
        df["language"].fillna("未知").value_counts().rename_axis("language").reset_index(name="count").to_dict("records"),
    )
    write_json(
        DERIVED_DIR / "category_distribution.json",
        df["category"].fillna("Other").value_counts().rename_axis("category").reset_index(name="count").to_dict("records"),
    )
    write_json(
        DERIVED_DIR / "health_scores.json",
        df[["full_name", "health_score", "growth_score", "maintenance_pressure"]]
        .sort_values("health_score", ascending=False)
        .to_dict("records"),
    )
    write_json(DERIVED_DIR / "insights.json", {"items": generate_insights(df)})


def dataframe_from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    df = normalize_repositories(records)
    for column in REPOSITORY_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[REPOSITORY_COLUMNS]


def initialize_store_from_legacy() -> pd.DataFrame:
    ensure_source_files()
    records = load_raw_repo_records()
    if not records:
        records = load_legacy_seed_records()
        if records:
            save_raw_repo_records(records)

    df = dataframe_from_records(records)
    if not df.empty:
        write_manifest(active_source="本地缓存数据", repo_count=len(df), data_mode="cache")
        write_snapshot(df, "cache")
        write_derived_files(df)
    return df


def load_cache_dataframe() -> pd.DataFrame:
    df = dataframe_from_records(load_raw_repo_records())
    if df.empty:
        df = initialize_store_from_legacy()
    return df


def save_dataset(
    records: list[dict[str, Any]],
    *,
    active_source: str,
    data_mode: str,
) -> pd.DataFrame:
    save_raw_repo_records(records)
    df = dataframe_from_records(records)
    write_manifest(active_source=active_source, repo_count=len(df), data_mode=data_mode)
    write_snapshot(df, data_mode)
    write_derived_files(df)
    return df


def load_online_source_config() -> dict[str, Any]:
    ensure_source_files()
    config = read_json(ONLINE_SOURCE_FILE, default_online_source())
    if not isinstance(config, dict):
        return default_online_source()
    merged = default_online_source()
    merged.update(config)
    return merged


def load_sample_records() -> list[dict[str, Any]]:
    ensure_source_files()
    source = read_json(SAMPLE_SOURCE_FILE, {})
    repo_names = source.get("repositories", []) if isinstance(source, dict) else []
    raw_records = load_raw_repo_records()
    if not repo_names:
        return raw_records
    wanted = {str(repo).strip() for repo in repo_names}
    sample = [record for record in raw_records if record.get("full_name") in wanted]
    return sample or raw_records
