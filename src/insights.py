from __future__ import annotations

import pandas as pd


def generate_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["当前数据源为空，请选择其他数据源。"]

    insights: list[str] = []
    language_counts = df["language"].fillna("未知").value_counts()
    if not language_counts.empty:
        top_languages = "、".join(language_counts.head(2).index.tolist())
        insights.append(f"当前样本主要集中在 {top_languages} 技术栈。")

    top_influence = df.sort_values("influence_score", ascending=False).iloc[0]
    insights.append(f"{top_influence['full_name']} 的生态影响力最高。")

    top_health = df.sort_values("health_score", ascending=False).iloc[0]
    insights.append(f"{top_health['full_name']} 当前健康评分领先。")

    top_pressure = df.sort_values("maintenance_pressure", ascending=False).iloc[0]
    insights.append(f"{top_pressure['full_name']} 的维护压力相对较高，需要重点观察。")

    category_counts = df["category"].fillna("Other").value_counts()
    if not category_counts.empty:
        insights.append(f"{category_counts.index[0]} 是当前样本中数量最多的项目类别。")

    active = df[df["activity_score"] >= df["activity_score"].median()]
    if not active.empty:
        active_category = active["category"].fillna("Other").value_counts().index[0]
        insights.append(f"{active_category} 类项目近期活跃度表现更突出。")

    return insights[:6]
