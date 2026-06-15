from __future__ import annotations

import sqlite3

import pandas as pd

try:
    from .config import DATABASE_PATH, ensure_database_directory, write_log
    from .data_store import initialize_store_from_legacy, load_cache_dataframe, write_derived_files
    from .transform import REPOSITORY_COLUMNS
except ImportError:
    from config import DATABASE_PATH, ensure_database_directory, write_log
    from data_store import initialize_store_from_legacy, load_cache_dataframe, write_derived_files
    from transform import REPOSITORY_COLUMNS


TABLE_NAME = "github_repositories"


def get_connection(create_parent: bool = False) -> sqlite3.Connection:
    if create_parent:
        ensure_database_directory()
    return sqlite3.connect(DATABASE_PATH)


def ensure_database() -> None:
    with get_connection(create_parent=True) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                name TEXT,
                owner TEXT,
                description TEXT,
                html_url TEXT,
                homepage TEXT,
                language TEXT,
                topics TEXT,
                license TEXT,
                stargazers_count INTEGER,
                forks_count INTEGER,
                watchers_count INTEGER,
                subscribers_count INTEGER,
                open_issues_count INTEGER,
                size INTEGER,
                created_at TEXT,
                updated_at TEXT,
                pushed_at TEXT,
                archived INTEGER,
                disabled INTEGER,
                default_branch TEXT,
                release_count INTEGER,
                latest_release_at TEXT,
                recent_commit_count_30d INTEGER,
                recent_commit_count_90d INTEGER,
                open_pr_count INTEGER,
                closed_pr_count INTEGER,
                contributor_count INTEGER,
                issue_close_rate REAL,
                avg_issue_close_days REAL,
                category TEXT,
                stars_per_day REAL,
                fork_star_ratio REAL,
                issue_star_ratio REAL,
                activity_score REAL,
                growth_score REAL,
                maintenance_pressure REAL,
                health_score REAL,
                ecosystem_score REAL,
                recency_score REAL,
                community_score REAL,
                influence_score REAL
            )
            """
        )


def save_repositories(df: pd.DataFrame) -> None:
    ensure_database()
    if df.empty:
        return

    for column in REPOSITORY_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    with get_connection() as conn:
        df[REPOSITORY_COLUMNS].to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    write_derived_files(df[REPOSITORY_COLUMNS])


def load_seed_repositories() -> pd.DataFrame:
    return load_cache_dataframe()


def bootstrap_database_from_seed() -> None:
    if DATABASE_PATH.exists():
        return

    seed_df = initialize_store_from_legacy()
    if seed_df.empty:
        return

    save_repositories(seed_df)


def load_repositories() -> pd.DataFrame:
    bootstrap_database_from_seed()
    if not DATABASE_PATH.exists():
        return pd.DataFrame(columns=REPOSITORY_COLUMNS)

    try:
        with get_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        write_log("error", "repository_load_failed", type(exc).__name__)
        return pd.DataFrame(columns=REPOSITORY_COLUMNS)

    for column in REPOSITORY_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[REPOSITORY_COLUMNS]
