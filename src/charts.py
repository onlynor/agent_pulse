from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


CHART_TEMPLATE = "plotly_dark"
CYAN = "#22d3ee"
BLUE = "#3b82f6"
VIOLET = "#8b5cf6"
GREEN = "#34d399"
AMBER = "#f59e0b"
RED = "#fb7185"
PANEL_BG = "rgba(8, 18, 45, 0.82)"
GRID = "rgba(148, 163, 184, 0.16)"
TEXT = "#dbeafe"
MUTED = "#93c5fd"

FOCUS_REPOSITORIES = [
    "openclaw/openclaw",
    "NousResearch/hermes-agent",
    "n8n-io/n8n",
    "langgenius/dify",
]


def _apply_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
            margin=dict(l=18, r=18, t=10, b=22),  # 移除标题后，顶部边距减小到 10
            title=None,  # 不显示内部标题
        font=dict(family="Microsoft YaHei, Arial, sans-serif", size=13, color=TEXT),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
        legend=dict(
            font=dict(color=MUTED),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, color=MUTED)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, color=MUTED)
    return fig


def empty_figure(message: str = "暂无数据") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color=MUTED, size=16),
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=320,
        margin=dict(l=18, r=18, t=10, b=22),
        title=None,
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def text_card(title: str, message: str, height: int = 320) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font=dict(color=TEXT, size=18),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=18, r=18, t=10, b=22),
        title=None,
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
    )
    return fig


def stars_by_repository(df: pd.DataFrame, limit: int = 12) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = df.sort_values("stargazers_count", ascending=False).head(limit)
    fig = px.bar(
        chart_df,
        x="stargazers_count",
        y="full_name",
        orientation="h",
        labels={"stargazers_count": "星标数", "full_name": "仓库"},
        title="热门仓库星标排行",
        color="stargazers_count",
        color_continuous_scale=["#0f172a", BLUE, CYAN],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>星标数：%{x:,}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _apply_layout(fig, 500)


def language_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = (
        df.groupby("language", dropna=False)
        .size()
        .reset_index(name="repositories")
        .sort_values("repositories", ascending=False)
    )
    if len(chart_df) == 1:
        language = chart_df.iloc[0]["language"]
        count = int(chart_df.iloc[0]["repositories"])
        return text_card("", f"当前筛选结果全部为 {language} 项目<br>仓库数量：{count}")

    # 改用水平条形图，避免饼图标签重叠问题
    fig = px.bar(
        chart_df.head(10),  # 只显示前 10 项
        x="repositories",
        y="language",
        orientation="h",
        labels={"repositories": "仓库数", "language": "语言"},
        color="repositories",
        color_continuous_scale=["#0f172a", BLUE, CYAN],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>仓库数：%{x}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _apply_layout(fig, 420)


def ecosystem_matrix(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = df.copy()
    fig = px.scatter(
        chart_df,
        x="influence_score",
        y="activity_score",
        size="stargazers_count",
        color="category",
        hover_name="full_name",
        labels={
            "influence_score": "影响力评分",
            "activity_score": "活跃度评分",
            "stargazers_count": "星标数",
            "category": "项目类别",
        },
        size_max=42,
        color_discrete_sequence=[CYAN, BLUE, VIOLET, GREEN, AMBER, RED, "#14b8a6", "#a78bfa"],
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.72)"), opacity=0.78),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "影响力：%{x:.1f}<br>"
            "活跃度：%{y:.1f}<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[-4, 104])
    fig.update_yaxes(range=[-4, 104])
    return _apply_layout(fig, 520)


def score_ranking(
    df: pd.DataFrame,
    score_column: str,
    title: str,
    color: str,
    limit: int = 10,
) -> go.Figure:
    if df.empty or score_column not in df.columns:
        return empty_figure()

    chart_df = df.sort_values(score_column, ascending=False).head(limit)
    fig = px.bar(
        chart_df,
        x=score_column,
        y="full_name",
        orientation="h",
        labels={score_column: "评分", "full_name": "仓库"},
        color=score_column,
        color_continuous_scale=["#0f172a", color],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>评分：%{x:.1f}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _apply_layout(fig, 390)


def health_score_ranking(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    return score_ranking(df, "health_score", "", GREEN, limit)


def growth_score_ranking(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    return score_ranking(df, "growth_score", "", CYAN, limit)


def maintenance_pressure_ranking(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    return score_ranking(df, "maintenance_pressure", "", RED, limit)


def category_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = (
        df.groupby("category", dropna=False)
        .size()
        .reset_index(name="repositories")
        .sort_values("repositories", ascending=False)
    )
    fig = px.bar(
        chart_df,
        x="repositories",
        y="category",
        orientation="h",
        labels={"repositories": "仓库数", "category": "项目类别"},
        color="repositories",
        color_continuous_scale=["#0f172a", BLUE, CYAN],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>仓库数：%{x}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _apply_layout(fig, 390)


def activity_scatter(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    fig = px.scatter(
        df,
        x="forks_count",
        y="open_issues_count",
        size="stargazers_count",
        color="language",
        hover_name="full_name",
        labels={
            "forks_count": "派生数",
            "open_issues_count": "开放问题",
            "stargazers_count": "星标数",
            "language": "主要语言",
        },
        title="生态活跃度气泡图",
        color_discrete_sequence=[CYAN, BLUE, VIOLET, GREEN, AMBER, RED],
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.75)"), opacity=0.82),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "派生数：%{x:,}<br>"
            "开放问题：%{y:,}<extra></extra>"
        ),
    )
    return _apply_layout(fig, 460)


def focus_project_compare(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    focus_df = df[df["full_name"].isin(FOCUS_REPOSITORIES)].copy()
    if focus_df.empty:
        return empty_figure("暂无重点项目数据")

    focus_df["短名称"] = focus_df["full_name"].str.split("/").str[-1]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=focus_df["短名称"],
            y=focus_df["stargazers_count"],
            name="星标数",
            marker_color=CYAN,
            hovertemplate="<b>%{x}</b><br>星标数：%{y:,}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=focus_df["短名称"],
            y=focus_df["forks_count"],
            name="派生数",
            marker_color=VIOLET,
            hovertemplate="<b>%{x}</b><br>派生数：%{y:,}<extra></extra>",
        )
    )
    fig.update_layout(
        title="重点项目影响力对比",
        barmode="group",
        yaxis_title="数量",
        xaxis_title="",
    )
    return _apply_layout(fig, 420)


def issue_pressure_bar(df: pd.DataFrame, limit: int = 10) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = df.sort_values("open_issues_count", ascending=False).head(limit)
    fig = px.bar(
        chart_df,
        x="open_issues_count",
        y="full_name",
        orientation="h",
        labels={"open_issues_count": "开放问题", "full_name": "仓库"},
        title="维护压力排行",
        color="open_issues_count",
        color_continuous_scale=["#0f172a", AMBER, RED],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>开放问题：%{x:,}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return _apply_layout(fig, 420)


def license_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return empty_figure()

    chart_df = (
        df.groupby("license", dropna=False)
        .size()
        .reset_index(name="repositories")
        .sort_values("repositories", ascending=False)
    )
    fig = px.bar(
        chart_df,
        x="license",
        y="repositories",
        labels={"license": "许可证", "repositories": "仓库数"},
        title="开源许可证分布",
        color="repositories",
        color_continuous_scale=["#0f172a", BLUE, GREEN],
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>仓库数：%{y}<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    return _apply_layout(fig, 360)
