"""基于 CSV 的仓库缓存存储。

本模块提供 CSV 读写能力，用单一文件替代分散的 JSON 文件。
优点：
- 单文件存储，避免大量 JSON 文件
- 批量读写更快
- 更便于版本管理和 diff
- 磁盘占用更小，避免重复字段名
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .config import RAW_DIR, write_log
except ImportError:
    from config import RAW_DIR, write_log


# CSV 文件路径。RAW_DIR 保留为 data/cache 的兼容别名。
RAW_REPOS_CSV = RAW_DIR / "repositories.csv"
BACKUP_REPOS_CSV = RAW_DIR / "repositories_backup.csv"

# 写入 CSV 的 GitHub 核心字段
CSV_FIELDS = [
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
]


def _extract_owner(record: dict[str, Any]) -> str:
    """从 GitHub API 响应中提取 owner login。"""
    owner = record.get("owner", {})
    if isinstance(owner, dict):
        return str(owner.get("login", ""))
    return str(owner or "")


def _extract_license(record: dict[str, Any]) -> str:
    """从 GitHub API 响应中提取许可证 SPDX ID。"""
    license_info = record.get("license")
    if isinstance(license_info, dict):
        return str(license_info.get("spdx_id") or license_info.get("key") or "")
    return str(license_info or "")


def _extract_topics(record: dict[str, Any]) -> str:
    """将 topics 列表转换为逗号分隔字符串。"""
    topics = record.get("topics", [])
    if isinstance(topics, list):
        return ", ".join(str(t) for t in topics if t)
    return str(topics or "")


def records_to_csv_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将 GitHub API 记录转换为适合 CSV 的扁平行。"""
    rows = []
    for record in records:
        row = {
            "id": record.get("id", ""),
            "full_name": record.get("full_name", ""),
            "name": record.get("name", ""),
            "owner": _extract_owner(record),
            "description": record.get("description", ""),
            "html_url": record.get("html_url", ""),
            "homepage": record.get("homepage", ""),
            "language": record.get("language", ""),
            "topics": _extract_topics(record),
            "license": _extract_license(record),
            "stargazers_count": record.get("stargazers_count", 0),
            "forks_count": record.get("forks_count", 0),
            "watchers_count": record.get("watchers_count", 0),
            "subscribers_count": record.get("subscribers_count", 0),
            "open_issues_count": record.get("open_issues_count", 0),
            "size": record.get("size", 0),
            "created_at": record.get("created_at", ""),
            "updated_at": record.get("updated_at", ""),
            "pushed_at": record.get("pushed_at", ""),
            "archived": record.get("archived", False),
            "disabled": record.get("disabled", False),
            "default_branch": record.get("default_branch", ""),
        }
        rows.append(row)
    return rows


def csv_rows_to_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将 CSV 行还原为类似 GitHub API 的记录格式以保持兼容。"""
    records = []
    for row in rows:
        # 重建 owner 对象
        owner_login = row.get("owner", "")
        owner = {"login": owner_login, "type": "User"} if owner_login else {}

        # 重建 license 对象
        license_spdx = row.get("license", "")
        license_obj = {"spdx_id": license_spdx, "key": license_spdx.lower()} if license_spdx else None

        # 重建 topics 列表
        topics_str = row.get("topics", "")
        topics = [t.strip() for t in topics_str.split(",") if t.strip()] if topics_str else []

        record = {
            "id": row.get("id"),
            "full_name": row.get("full_name", ""),
            "name": row.get("name", ""),
            "owner": owner,
            "description": row.get("description", ""),
            "html_url": row.get("html_url", ""),
            "homepage": row.get("homepage", ""),
            "language": row.get("language", ""),
            "topics": topics,
            "license": license_obj,
            "stargazers_count": int(row.get("stargazers_count", 0) or 0),
            "forks_count": int(row.get("forks_count", 0) or 0),
            "watchers_count": int(row.get("watchers_count", 0) or 0),
            "subscribers_count": int(row.get("subscribers_count", 0) or 0),
            "open_issues_count": int(row.get("open_issues_count", 0) or 0),
            "size": int(row.get("size", 0) or 0),
            "created_at": row.get("created_at", ""),
            "updated_at": row.get("updated_at", ""),
            "pushed_at": row.get("pushed_at", ""),
            "archived": bool(row.get("archived", False)),
            "disabled": bool(row.get("disabled", False)),
            "default_branch": row.get("default_branch", ""),
        }
        records.append(record)
    return records


def save_repos_to_csv(records: list[dict[str, Any]], path: Path = RAW_REPOS_CSV) -> bool:
    """保存仓库记录到 CSV 文件。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = records_to_csv_rows(records)

        if not rows:
            write_log("warning", "csv_save_empty", "no records to save")
            return False

        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        write_log("info", "csv_save_success", f"saved {len(rows)} records to {path.name}")
        return True

    except (OSError, csv.Error) as exc:
        write_log("error", "csv_save_failed", f"{path.name}: {type(exc).__name__}")
        return False


def load_repos_from_csv(path: Path = RAW_REPOS_CSV) -> list[dict[str, Any]]:
    """从 CSV 文件加载仓库记录。"""
    if not path.exists():
        write_log("info", "csv_not_found", f"{path.name} does not exist")
        return []

    try:
        df = pd.read_csv(path, encoding="utf-8", keep_default_na=False)
        rows = df.to_dict("records")
        records = csv_rows_to_records(rows)
        write_log("info", "csv_load_success", f"loaded {len(records)} records from {path.name}")
        return records

    except (OSError, pd.errors.ParserError, ValueError) as exc:
        write_log("error", "csv_load_failed", f"{path.name}: {type(exc).__name__}")
        return []


def migrate_json_to_csv(json_records: list[dict[str, Any]], backup: bool = True) -> bool:
    """将已有 JSON 记录迁移为 CSV 格式。

    参数：
        json_records: 从 JSON 文件加载的记录列表
        backup: 覆盖前是否创建 CSV 备份

    返回：
        迁移成功时返回 True
    """
    if not json_records:
        write_log("warning", "csv_migration_empty", "no JSON records provided")
        return False

    # 按需在覆盖前创建备份
    if backup and RAW_REPOS_CSV.exists():
        try:
            import shutil
            shutil.copy2(RAW_REPOS_CSV, BACKUP_REPOS_CSV)
            write_log("info", "csv_backup_created", f"{BACKUP_REPOS_CSV.name}")
        except OSError as exc:
            write_log("warning", "csv_backup_failed", type(exc).__name__)

    # 保存为 CSV
    success = save_repos_to_csv(json_records, RAW_REPOS_CSV)

    if success:
        write_log("info", "csv_migration_success", f"migrated {len(json_records)} records to CSV")

    return success


def verify_csv_integrity() -> dict[str, Any]:
    """校验 CSV 文件完整性并返回统计信息。

    返回：
        包含 exists、record_count、has_duplicates、missing_fields 的字典
    """
    if not RAW_REPOS_CSV.exists():
        return {
            "exists": False,
            "record_count": 0,
            "has_duplicates": False,
            "missing_fields": [],
        }

    try:
        df = pd.read_csv(RAW_REPOS_CSV, encoding="utf-8", keep_default_na=False)

        # 检查重复仓库
        has_duplicates = df["full_name"].duplicated().any()

        # 检查必填字段缺失
        missing_fields = [field for field in ["id", "full_name", "name"] if field not in df.columns]

        return {
            "exists": True,
            "record_count": len(df),
            "has_duplicates": has_duplicates,
            "missing_fields": missing_fields,
            "columns": list(df.columns),
        }

    except Exception as exc:
        write_log("error", "csv_verification_failed", type(exc).__name__)
        return {
            "exists": True,
            "record_count": 0,
            "has_duplicates": False,
            "missing_fields": [],
            "error": str(exc),
        }
