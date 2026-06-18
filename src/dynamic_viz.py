"""AgentPulse 仪表盘的动态可视化组件。"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

try:
    from .charts import CHART_TEMPLATE, CYAN, GRID, MUTED, PANEL_BG, TEXT
except ImportError:
    from charts import CHART_TEMPLATE, CYAN, GRID, MUTED, PANEL_BG, TEXT


BAR_COLORS = [
    "#22d3ee",
    "#2ec4e6",
    "#3ab5de",
    "#46a6d6",
    "#5297ce",
    "#5e88c6",
    "#6a79be",
    "#766ab6",
    "#6a6bae",
    "#5e5ca6",
    "#824ca6",
    "#963d9e",
    "#aa2e96",
    "#be1f8e",
    "#ca017e",
]


def select_trending_repos(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """选择星标数最高的仓库，并按升序返回以便从左到右升高。"""
    if df.empty or "stargazers_count" not in df.columns:
        return pd.DataFrame()

    df_clean = df.copy()
    df_clean["stargazers_count"] = (
        pd.to_numeric(df_clean["stargazers_count"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    top = df_clean.nlargest(top_n, "stargazers_count").copy()
    top["rank"] = range(1, len(top) + 1)
    return top.sort_values("stargazers_count", ascending=True)


def _empty_bar_figure(message: str) -> go.Figure:
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
        height=450,
        margin=dict(l=18, r=18, t=10, b=22),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _bar_trace(
    chart_df: pd.DataFrame,
    colors: list[str],
    values: list[int],
    active_idx: int | None = None,
) -> go.Bar:
    line_colors = []
    line_widths = []
    for idx in range(len(chart_df)):
        line_colors.append("rgba(255,255,255,0.55)" if idx == active_idx else "rgba(255,255,255,0.08)")
        line_widths.append(2.5 if idx == active_idx else 0.5)

    return go.Bar(
        x=chart_df["axis_label"].tolist(),
        y=values,
        customdata=[
            [
                str(row["full_name"]),
                int(row["stargazers_count"]),
                int(row["rank"]),
                str(row["html_url"]),
            ]
            for _, row in chart_df.iterrows()
        ],
        text=[f"{value:,}" if value > 0 else "" for value in values],
        textposition="outside",
        cliponaxis=False,
        marker=dict(
            color=colors,
            line=dict(color=line_colors, width=line_widths),
        ),
        showlegend=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "排名: Top %{customdata[2]}<br>"
            "⭐ 星标: %{customdata[1]:,}<br>"
            "<a href='%{customdata[3]}' target='_blank'>打开 GitHub</a><br>"
            "<extra></extra>"
        ),
    )


def create_animated_star_trend(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """创建 Top N 仓库真实星标数的竖向柱状动画图。"""
    if df.empty:
        return _empty_bar_figure("暂无数据")
    if "full_name" not in df.columns or "stargazers_count" not in df.columns:
        return _empty_bar_figure("暂无足够数据")

    chart_df = select_trending_repos(df, top_n).copy()
    if chart_df.empty:
        return _empty_bar_figure("暂无足够数据")

    chart_df["short_name"] = chart_df["full_name"].astype(str).str.split("/").str[-1]
    chart_df["axis_label"] = chart_df["short_name"]
    chart_df["html_url"] = chart_df["full_name"].map(lambda name: f"https://github.com/{name}")
    colors = BAR_COLORS[: len(chart_df)]
    target_values = chart_df["stargazers_count"].astype(int).tolist()
    x_labels = chart_df["axis_label"].tolist()

    frames = []
    slider_steps = []
    growth_steps = 8
    for active_idx, target in enumerate(target_values):
        for step in range(1, growth_steps + 1):
            progress = step / growth_steps
            eased = progress * progress * (3 - 2 * progress)
            values = (
                target_values[:active_idx]
                + [int(target * eased)]
                + [0] * (len(target_values) - active_idx - 1)
            )
            frame_name = f"{active_idx + 1}-{step}"
            frames.append(
                go.Frame(
                    data=[_bar_trace(chart_df, colors, values, active_idx)],
                    name=frame_name,
                )
            )
        slider_steps.append(
            {
                "args": [
                    [frames[-1].name],
                    {
                        "frame": {"duration": 0, "redraw": True},
                        "mode": "immediate",
                    },
                ],
                "label": f"Top {int(chart_df.iloc[active_idx]['rank'])}",
                "method": "animate",
            }
        )

    frame_names = [frame.name for frame in frames]
    fig = go.Figure(data=[_bar_trace(chart_df, colors, target_values)], frames=frames)

    fig.update_layout(
        template=CHART_TEMPLATE,
        height=540,
        margin=dict(l=45, r=30, t=20, b=95),
        font=dict(family="Microsoft YaHei, Arial, sans-serif", size=13, color=TEXT),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
        xaxis=dict(
            title="",
            gridcolor=GRID,
            zerolinecolor=GRID,
            color=MUTED,
            categoryorder="array",
            categoryarray=x_labels,
            tickangle=-30,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="",
            gridcolor=GRID,
            zerolinecolor=GRID,
            color=MUTED,
            tickformat=",",
            tickfont=dict(size=11),
            rangemode="tozero",
            range=[0, max(target_values) * 1.12],
        ),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="rgba(8, 18, 45, 0.95)",
            bordercolor=CYAN,
            font=dict(color=TEXT, size=12),
        ),
        bargap=0.28,
        sliders=[
            {
                "active": len(frames) - 1,
                "steps": slider_steps,
                "x": 0.02,
                "y": -0.08,
                "len": 0.96,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"b": 15, "t": 15},
                "currentvalue": {
                    "visible": True,
                    "prefix": "  ",
                    "xanchor": "left",
                    "font": {"size": 13, "color": TEXT},
                },
                "transition": {"duration": 0},
                "bgcolor": "rgba(15, 23, 42, 0.7)",
                "bordercolor": CYAN,
                "borderwidth": 1.5,
                "tickcolor": CYAN,
                "font": {"color": MUTED, "size": 9},
            }
        ],
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶",
                        "method": "animate",
                        "args": [
                            frame_names,
                            {
                                "frame": {"duration": 70, "redraw": True},
                                "fromcurrent": False,
                                "mode": "immediate",
                                "transition": {"duration": 45},
                            },
                        ],
                    },
                    {
                        "label": "■",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 5},
                "x": 0.01,
                "y": 1.02,
                "xanchor": "left",
                "yanchor": "bottom",
                "bgcolor": "rgba(3, 18, 29, 0.9)",
                "bordercolor": CYAN,
                "borderwidth": 2,
                "font": dict(color=TEXT, size=16),
            }
        ],
    )

    fig.add_annotation(
        text=f"已采集项目 {len(chart_df)} 个 · 仅按 GitHub 星标数排序 · 悬停可打开项目链接",
        xref="paper",
        yref="paper",
        x=1.0,
        y=0.0,
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        font=dict(color=MUTED, size=9),
    )

    return fig
