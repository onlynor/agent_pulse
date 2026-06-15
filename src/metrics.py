from __future__ import annotations

import pandas as pd


def repository_summary(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {
            "repositories": 0,
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
        }

    return {
        "repositories": int(len(df)),
        "stars": int(df["stargazers_count"].sum()),
        "forks": int(df["forks_count"].sum()),
        "open_issues": int(df["open_issues_count"].sum()),
    }
