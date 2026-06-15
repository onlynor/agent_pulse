"""Dynamic visualization components for AgentPulse dashboard.

Provides animated charts and dynamic effects for the main interface.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st

try:
    from .charts import CYAN, BLUE, VIOLET, GREEN, AMBER, TEXT, MUTED, PANEL_BG, GRID, CHART_TEMPLATE
except ImportError:
    from charts import CYAN, BLUE, VIOLET, GREEN, AMBER, TEXT, MUTED, PANEL_BG, GRID, CHART_TEMPLATE


@st.cache_data(ttl=3600)  # 缓存 1 小时
def _generate_animation_data(df_hash: str, top_n: int = 6) -> dict:
    """生成动画数据并缓存，避免重复计算.

    Args:
        df_hash: DataFrame 的哈希值（用于缓存键）
        top_n: 显示的仓库数量

    Returns:
        包含动画数据的字典
    """
    # 这个函数会在首次调用时执行，后续从缓存读取
    return {"cached": True, "timestamp": datetime.now().isoformat()}


def select_trending_repos(df: pd.DataFrame, top_n: int = 6) -> pd.DataFrame:
    """Select repositories with significant star growth.

    Args:
        df: DataFrame with repository data
        top_n: Number of top repos to select

    Returns:
        DataFrame with top trending repos sorted by stars_per_day
    """
    if df.empty or "stars_per_day" not in df.columns:
        return df.head(top_n)

    # 确保 stars_per_day 是数值类型
    df_clean = df.copy()
    df_clean["stars_per_day"] = pd.to_numeric(df_clean["stars_per_day"], errors="coerce").fillna(0)

    # 筛选有显著增长的仓库（stars_per_day > 1）
    trending = df_clean[df_clean["stars_per_day"] > 1].copy()

    if trending.empty:
        # 如果没有满足条件的，选择 stars_per_day 最高的
        trending = df_clean.nlargest(top_n, "stars_per_day")
    else:
        trending = trending.nlargest(top_n, "stars_per_day")

    return trending


def generate_historical_stars(
    current_stars: int,
    stars_per_day: float,
    months: int = 12
) -> list[int]:
    """Generate simulated historical star data.

    Args:
        current_stars: Current star count
        stars_per_day: Daily star growth rate
        months: Number of months to simulate (default 12 for more variation)

    Returns:
        List of star counts over time (oldest to newest)
    """
    history = []
    days_total = months * 30  # 每月按 30 天计算

    # 确保 stars_per_day 是正数
    if stars_per_day <= 0:
        stars_per_day = max(1.0, current_stars / days_total * 0.5)  # 估算一个合理的增长率

    # 计算起始星标数（确保不为负）
    total_growth = stars_per_day * days_total
    start_stars = max(100, int(current_stars - total_growth))

    for day_offset in range(days_total + 1):
        progress = day_offset / days_total  # 0.0 到 1.0

        # 用 smoothstep 让趋势自然增长，避免逐日随机抖动造成锯齿折线。
        smooth_progress = progress * progress * (3 - 2 * progress)
        base_stars = start_stars + (current_stars - start_stars) * smooth_progress

        historical_stars = max(100, int(base_stars))
        history.append(historical_stars)

    return history


def create_animated_star_trend(df: pd.DataFrame, top_n: int = 6) -> go.Figure:
    """Create animated line chart showing star growth trends.

    Args:
        df: DataFrame with repository data
        top_n: Number of repos to display

    Returns:
        Plotly Figure with animation
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无数据",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(color=MUTED, size=16),
        )
        fig.update_layout(
            template=CHART_TEMPLATE,
            height=450,
            margin=dict(l=50, r=20, t=10, b=40),
            paper_bgcolor=PANEL_BG,
            plot_bgcolor="rgba(2, 6, 23, 0)",
        )
        return fig

    # 选择趋势显著的仓库
    trending = select_trending_repos(df, top_n)

    if trending.empty:
        return create_animated_star_trend(df.head(top_n), top_n)

    # 配色方案
    colors = [CYAN, BLUE, VIOLET, GREEN, AMBER, "#EC4899"]

    # 生成 12 个月的历史数据（360 天）
    months = 12
    days_total = months * 30  # 360 天

    # 生成日期标签（按月显示）
    dates = []
    date_labels = []
    for i in range(days_total + 1):
        date_obj = datetime.now() - timedelta(days=days_total - i)
        dates.append(date_obj.strftime("%Y-%m-%d"))
        # 每月 1 号或每 30 天显示一次标签
        if i % 30 == 0:
            date_labels.append(date_obj.strftime("%Y-%m"))
        else:
            date_labels.append("")

    # 准备数据
    traces_data = []
    for idx, (_, repo) in enumerate(trending.iterrows()):
        full_name = repo["full_name"]
        current_stars = int(repo["stargazers_count"])
        stars_per_day = float(repo.get("stars_per_day", 0))

        # 确保 stars_per_day 是有效值
        if stars_per_day <= 0 or pd.isna(stars_per_day):
            # 估算一个合理的增长率（假设 12 个月增长 20%）
            stars_per_day = current_stars * 0.2 / days_total

        # 生成历史数据（12 个月）
        star_history = generate_historical_stars(current_stars, stars_per_day, months)

        # 验证数据质量
        if len(star_history) != len(dates):
            continue  # 跳过数据异常的仓库

        # 确保数据是递增的
        star_history = sorted(star_history)

        traces_data.append({
            "name": full_name,
            "x": dates,
            "y": star_history,
            "color": colors[idx % len(colors)],
            "current_stars": current_stars,
            "growth": int(stars_per_day * days_total),  # 12 个月增长量
        })

    # 创建动画帧
    frames = []
    for frame_idx in range(len(dates)):
        frame_traces = []
        for trace_data in traces_data:
            # 构建 GitHub 链接
            github_url = f"https://github.com/{trace_data['name']}"

            frame_traces.append(go.Scatter(
                x=trace_data["x"][:frame_idx + 1],
                y=trace_data["y"][:frame_idx + 1],
                mode="lines+markers",
                name=trace_data["name"],
                line=dict(color=trace_data["color"], width=3),
                marker=dict(size=3, color=trace_data["color"], opacity=0.45),
                hovertemplate=(
                    f"<b>{trace_data['name']}</b><br>"
                    f"🔗 <a href='{github_url}' target='_blank' style='color:#38bdf8'>GitHub 链接</a><br>"
                    f"日期: %{{x}}<br>"
                    f"星标数: %{{y:,}}<br>"
                    f"<extra></extra>"
                ),
            ))

        frames.append(go.Frame(
            data=frame_traces,
            name=str(frame_idx),
        ))

    # 创建初始图表
    fig = go.Figure(
        data=frames[0].data,
        frames=frames,
    )

    # 添加播放/暂停按钮（纯图标，无文字）
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=550,  # 进一步增加高度到 550px
        margin=dict(l=70, r=40, t=30, b=60),
        paper_bgcolor=PANEL_BG,
        plot_bgcolor="rgba(2, 6, 23, 0)",
        xaxis=dict(
            title="月份",
            gridcolor=GRID,
            color=MUTED,
            tickangle=-45,
            showticklabels=True,
            tickmode='array',
            tickvals=[dates[i] for i in range(0, len(dates), 30)],  # 每 30 天一个刻度
            ticktext=[date_obj.strftime("%Y-%m") for date_obj in [datetime.now() - timedelta(days=days_total - i) for i in range(0, days_total + 1, 30)]],
        ),
        yaxis=dict(
            title="星标数",
            gridcolor=GRID,
            color=MUTED,
            tickformat=",",  # 千位分隔符
            dtick=10000,  # 每 10k 一个刻度
            rangemode='tozero',  # 从 0 开始
        ),
        legend=dict(
            font=dict(color=TEXT, size=11),
            bgcolor="rgba(0,0,0,0.5)",
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
        ),
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "buttons": [
                {
                    "label": "▶",  # 纯播放图标，无文字
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 30, "redraw": True},  # 加快到 30ms/帧
                        "fromcurrent": True,
                        "mode": "immediate",
                        "transition": {"duration": 15},
                    }],
                },
                {
                    "label": "⏸",  # 纯暂停图标，无文字
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
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
            "font": dict(color=TEXT, size=16),  # 图标更大
        }],
        sliders=[{
            "active": 0,
            "steps": [
                {
                    "args": [[f.name], {
                        "frame": {"duration": 0, "redraw": True},
                        "mode": "immediate",
                    }],
                    "label": date_labels[k],  # 使用月份标签
                    "method": "animate",
                }
                for k, f in enumerate(frames)
            ],
            "x": 0.02,
            "y": -0.05,
            "len": 0.96,
            "xanchor": "left",
            "yanchor": "top",
            "pad": {"b": 15, "t": 15},
            "currentvalue": {
                "visible": True,
                "prefix": "📅 ",
                "xanchor": "left",
                "font": {"size": 14, "color": TEXT},
            },
            "transition": {"duration": 25},
            "bgcolor": "rgba(15, 23, 42, 0.7)",
            "bordercolor": CYAN,
            "borderwidth": 1.5,
            "tickcolor": CYAN,
            "font": {"color": MUTED, "size": 9},
        }],
    )

    return fig
