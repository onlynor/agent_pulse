from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def _parse_time(value: object) -> pd.Timestamp:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return pd.Timestamp(datetime.now(timezone.utc))
    return parsed


def _normalize(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0).astype(float)
    minimum = numeric.min()
    maximum = numeric.max()
    if maximum <= minimum:
        return pd.Series([50.0] * len(numeric), index=numeric.index)
    return ((numeric - minimum) / (maximum - minimum) * 100).round(2)


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()
    now = pd.Timestamp(datetime.now(timezone.utc))
    created_at = result["created_at"].map(_parse_time)
    updated_at = result["updated_at"].map(_parse_time)
    pushed_at = result["pushed_at"].map(_parse_time)

    age_days = (now - created_at).dt.days.clip(lower=1)
    inactive_days = (now - pushed_at).dt.days.clip(lower=0)
    update_days = (now - updated_at).dt.days.clip(lower=0)

    stars = pd.to_numeric(result["stargazers_count"], errors="coerce").fillna(0)
    forks = pd.to_numeric(result["forks_count"], errors="coerce").fillna(0)
    issues = pd.to_numeric(result["open_issues_count"], errors="coerce").fillna(0)
    watchers = pd.to_numeric(result["watchers_count"], errors="coerce").fillna(0)
    subscribers = pd.to_numeric(result.get("subscribers_count", 0), errors="coerce").fillna(0)
    recent_30 = pd.to_numeric(result.get("recent_commit_count_30d", 0), errors="coerce").fillna(0)
    recent_90 = pd.to_numeric(result.get("recent_commit_count_90d", 0), errors="coerce").fillna(0)
    contributors = pd.to_numeric(result.get("contributor_count", 0), errors="coerce").fillna(0)

    result["stars_per_day"] = (stars / age_days).round(4)
    result["fork_star_ratio"] = (forks / stars.clip(lower=1)).round(4)
    result["issue_star_ratio"] = (issues / stars.clip(lower=1)).round(4)

    influence = _normalize(stars) * 0.68 + _normalize(forks) * 0.22 + _normalize(watchers + subscribers) * 0.10
    activity = _normalize(recent_30 * 2 + recent_90 + (100 - inactive_days.clip(upper=100)))
    growth = _normalize(result["stars_per_day"]) * 0.72 + _normalize(recent_30) * 0.28
    community = _normalize(forks) * 0.45 + _normalize(contributors) * 0.30 + _normalize(watchers + subscribers) * 0.25
    recency = (100 - update_days.clip(upper=100)).astype(float)
    pressure = _normalize(issues * 0.7 + result["issue_star_ratio"] * 10000 * 0.3)

    result["influence_score"] = influence.round(2)
    result["activity_score"] = activity.round(2)
    result["growth_score"] = growth.round(2)
    result["community_score"] = community.round(2)
    result["recency_score"] = recency.round(2)
    result["maintenance_pressure"] = pressure.round(2)
    result["health_score"] = (
        result["activity_score"] * 0.30
        + result["recency_score"] * 0.25
        + result["community_score"] * 0.25
        + (100 - result["maintenance_pressure"]) * 0.20
    ).round(2)
    result["ecosystem_score"] = (
        result["influence_score"] * 0.35
        + result["activity_score"] * 0.25
        + result["growth_score"] * 0.20
        + result["health_score"] * 0.20
    ).round(2)
    return result
