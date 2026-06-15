"""迁移脚本：旧 JSON 文件 -> CSV 格式。

用于把可选的旧 JSON 仓库文件迁移为适合 git 管理的本地 CSV 缓存。

用法：
    python -m src.migrate_to_csv [--verify-only] [--no-backup]

选项：
    --verify-only: 只校验 CSV 完整性，不执行迁移
    --no-backup: 迁移前不创建备份
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 支持脚本独立执行时导入 src 内模块
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from csv_store import (
    RAW_REPOS_CSV,
    BACKUP_REPOS_CSV,
    load_repos_from_csv,
    migrate_json_to_csv,
    verify_csv_integrity,
)
from data_store import load_raw_repo_records


def print_status(message: str, level: str = "info") -> None:
    """打印带颜色的状态信息。"""
    colors = {
        "info": "\033[36m",  # 青色
        "success": "\033[32m",  # 绿色
        "warning": "\033[33m",  # 黄色
        "error": "\033[31m",  # 红色
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    # 使用 ASCII 标记以兼容 Windows 控制台
    message = message.replace("✓", "[OK]").replace("✗", "[X]").replace("⚠", "[!]")
    print(f"{color}{message}{reset}", flush=True)


def verify_only() -> int:
    """校验 CSV 完整性并打印报告。"""
    print_status("\n=== CSV Integrity Check ===", "info")

    stats = verify_csv_integrity()

    if not stats["exists"]:
        print_status(f"✗ CSV file does not exist: {RAW_REPOS_CSV}", "warning")
        print_status("  Run migration without --verify-only to create it.", "info")
        return 1

    print_status(f"✓ CSV file exists: {RAW_REPOS_CSV}", "success")
    print_status(f"  Records: {stats['record_count']}", "info")

    if stats.get("error"):
        print_status(f"✗ Parse error: {stats['error']}", "error")
        return 1

    if stats["has_duplicates"]:
        print_status("✗ Contains duplicate full_name entries", "warning")
    else:
        print_status("✓ No duplicates found", "success")

    if stats["missing_fields"]:
        print_status(f"✗ Missing required fields: {stats['missing_fields']}", "error")
        return 1
    else:
        print_status("✓ All required fields present", "success")

    print_status(f"\nColumns ({len(stats.get('columns', []))}):", "info")
    for col in stats.get("columns", [])[:10]:
        print(f"  - {col}")
    if len(stats.get("columns", [])) > 10:
        print(f"  ... and {len(stats['columns']) - 10} more")

    print()
    return 0


def run_migration(create_backup: bool = True) -> int:
    """执行 JSON 到 CSV 的迁移。"""
    print_status("\n=== JSON to CSV Migration ===", "info")

    # 加载 JSON 记录
    print_status("Loading legacy JSON records if available...", "info")
    json_records = load_raw_repo_records()

    if not json_records:
        print_status("✗ No JSON records found to migrate", "error")
        return 1

    print_status(f"✓ Loaded {len(json_records)} JSON records", "success")

    # 检查 CSV 是否已存在
    if RAW_REPOS_CSV.exists():
        print_status(f"⚠ CSV file already exists: {RAW_REPOS_CSV}", "warning")
        existing = load_repos_from_csv()
        print_status(f"  Existing CSV contains {len(existing)} records", "info")

        if create_backup:
            print_status(f"  Creating backup: {BACKUP_REPOS_CSV}", "info")

    # 执行迁移
    print_status("\nMigrating to CSV format...", "info")
    success = migrate_json_to_csv(json_records, backup=create_backup)

    if not success:
        print_status("✗ Migration failed", "error")
        return 1

    print_status(f"✓ Migration successful: {len(json_records)} records", "success")

    # 校验迁移结果
    print_status("\nVerifying migrated data...", "info")
    csv_records = load_repos_from_csv()

    if len(csv_records) != len(json_records):
        print_status(
            f"✗ Record count mismatch: JSON={len(json_records)}, CSV={len(csv_records)}",
            "error",
        )
        return 1

    print_status(f"✓ Verification passed: {len(csv_records)} records", "success")

    # 抽样对比
    if csv_records and json_records:
        json_sample = json_records[0]
        csv_sample = csv_records[0]
        print_status("\nSample comparison (first record):", "info")
        print_status(f"  JSON full_name: {json_sample.get('full_name')}", "info")
        print_status(f"  CSV full_name:  {csv_sample.get('full_name')}", "info")
        print_status(f"  JSON stars:     {json_sample.get('stargazers_count')}", "info")
        print_status(f"  CSV stars:      {csv_sample.get('stargazers_count')}", "info")

    print_status(f"\n✓ Migration complete!", "success")
    print_status(f"  CSV file: {RAW_REPOS_CSV}", "info")
    if create_backup and BACKUP_REPOS_CSV.exists():
        print_status(f"  Backup:   {BACKUP_REPOS_CSV}", "info")

    print()
    return 0


def main() -> int:
    """主入口。"""
    parser = argparse.ArgumentParser(
        description="Migrate repository data from JSON files to CSV format"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify CSV integrity without migrating",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before migration",
    )

    args = parser.parse_args()

    if args.verify_only:
        return verify_only()

    return run_migration(create_backup=not args.no_backup)


if __name__ == "__main__":
    sys.exit(main())
