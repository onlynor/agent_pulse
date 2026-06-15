"""Migration script: legacy JSON files -> CSV format.

Run this script to migrate optional legacy JSON repository files to the
git-friendly local cache CSV.

Usage:
    python -m src.migrate_to_csv [--verify-only] [--no-backup]

Options:
    --verify-only: Check CSV integrity without migrating
    --no-backup: Skip creating backup before migration
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for standalone execution
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
    """Print colored status message."""
    colors = {
        "info": "\033[36m",  # Cyan
        "success": "\033[32m",  # Green
        "warning": "\033[33m",  # Yellow
        "error": "\033[31m",  # Red
    }
    reset = "\033[0m"
    color = colors.get(level, "")
    # Use ASCII symbols for Windows compatibility
    message = message.replace("✓", "[OK]").replace("✗", "[X]").replace("⚠", "[!]")
    print(f"{color}{message}{reset}", flush=True)


def verify_only() -> int:
    """Verify CSV integrity and print report."""
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
    """Run the JSON to CSV migration."""
    print_status("\n=== JSON to CSV Migration ===", "info")

    # Load JSON records
    print_status("Loading legacy JSON records if available...", "info")
    json_records = load_raw_repo_records()

    if not json_records:
        print_status("✗ No JSON records found to migrate", "error")
        return 1

    print_status(f"✓ Loaded {len(json_records)} JSON records", "success")

    # Check if CSV already exists
    if RAW_REPOS_CSV.exists():
        print_status(f"⚠ CSV file already exists: {RAW_REPOS_CSV}", "warning")
        existing = load_repos_from_csv()
        print_status(f"  Existing CSV contains {len(existing)} records", "info")

        if create_backup:
            print_status(f"  Creating backup: {BACKUP_REPOS_CSV}", "info")

    # Run migration
    print_status("\nMigrating to CSV format...", "info")
    success = migrate_json_to_csv(json_records, backup=create_backup)

    if not success:
        print_status("✗ Migration failed", "error")
        return 1

    print_status(f"✓ Migration successful: {len(json_records)} records", "success")

    # Verify result
    print_status("\nVerifying migrated data...", "info")
    csv_records = load_repos_from_csv()

    if len(csv_records) != len(json_records):
        print_status(
            f"✗ Record count mismatch: JSON={len(json_records)}, CSV={len(csv_records)}",
            "error",
        )
        return 1

    print_status(f"✓ Verification passed: {len(csv_records)} records", "success")

    # Sample comparison
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
    """Main entry point."""
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
