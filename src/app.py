from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

GENERIC_ERROR_MESSAGE = "数据加载失败，请点击刷新按钮重试"
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def load_module(name: str):
    try:
        if __package__:
            return import_module(f".{name}", package=__package__)
        return import_module(name)
    except Exception:
        return import_module(name)


def safe_write_log(event: str, detail: object = "") -> None:
    try:
        config = load_module("config")
        config.write_log("error", event, detail)
    except Exception:
        pass


def load_dependencies() -> dict[str, object] | None:
    try:
        charts = load_module("charts")
        collect_data = load_module("collect_data")
        database = load_module("database")
        data_store = load_module("data_store")
        dynamic_viz = load_module("dynamic_viz")
        insights = load_module("insights")
        metrics = load_module("metrics")
        return {
            "category_distribution": charts.category_distribution,
            "ecosystem_matrix": charts.ecosystem_matrix,
            "growth_score_ranking": charts.growth_score_ranking,
            "health_score_ranking": charts.health_score_ranking,
            "language_distribution": charts.language_distribution,
            "maintenance_pressure_ranking": charts.maintenance_pressure_ranking,
            "update_data_source": collect_data.update_data_source,
            "load_repositories": database.load_repositories,
            "read_manifest": data_store.read_manifest,
            "generate_insights": insights.generate_insights,
            "repository_summary": metrics.repository_summary,
            "create_animated_star_trend": dynamic_viz.create_animated_star_trend,
            "write_log": load_module("config").write_log,
        }
    except Exception as exc:
        safe_write_log("dashboard_dependency_load_failed", type(exc).__name__)
        return None


def apply_page_style() -> None:
    css = (SRC_DIR / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def format_time(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return text.replace("T", " ").replace("Z", "")


def render_sidebar_nav() -> None:
    """渲染显式导航标签，避免使用 Streamlit 默认文件名。"""
    with st.sidebar:
        st.page_link("app.py", label="首页")
        st.page_link("pages/2_📊_细分图表分析.py", label="细分图表分析")
        st.page_link("pages/3_📋_原始数据.py", label="原始数据")
        st.divider()


def filter_repositories(
    df: pd.DataFrame,
    languages: list[str],
    categories: list[str],
    keyword: str,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()
    if languages:
        filtered = filtered[filtered["language"].isin(languages)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]

    keyword = keyword.strip().lower()
    if keyword:
        name_match = filtered["full_name"].str.lower().str.contains(keyword, na=False)
        desc_match = filtered["description"].str.lower().str.contains(keyword, na=False)
        topic_match = filtered["topics"].str.lower().str.contains(keyword, na=False)
        filtered = filtered[name_match | desc_match | topic_match]
    return filtered


def make_display_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "full_name",
        "category",
        "language",
        "stargazers_count",
        "forks_count",
        "open_issues_count",
        "health_score",
        "growth_score",
        "maintenance_pressure",
        "updated_at",
    ]
    display_df = df[columns].copy()
    display_df["updated_at"] = display_df["updated_at"].map(format_time)
    return display_df.rename(
        columns={
            "full_name": "仓库",
            "category": "项目类别",
            "language": "主要语言",
            "stargazers_count": "星标数",
            "forks_count": "派生数",
            "open_issues_count": "开放问题",
            "health_score": "健康评分",
            "growth_score": "增长评分",
            "maintenance_pressure": "维护压力",
            "updated_at": "更新时间",
        }
    )


def render_kpis(df: pd.DataFrame, filtered_df: pd.DataFrame, summary: dict[str, int]) -> None:
    avg_health = float(filtered_df["health_score"].mean()) if not filtered_df.empty else 0
    avg_growth = float(filtered_df["growth_score"].mean()) if not filtered_df.empty else 0
    categories = int(filtered_df["category"].nunique()) if not filtered_df.empty else 0
    kpis = [
        ("仓库数量", f"{summary['repositories']:,}", f"本地数据集 {len(df):,}"),
        ("星标总数", f"{summary['stars']:,}", "社区关注度"),
        ("派生总数", f"{summary['forks']:,}", "开发参与度"),
        ("开放问题", f"{summary['open_issues']:,}", "维护压力"),
        ("平均健康", f"{avg_health:.1f}", "综合评分"),
        ("类别数量", f"{categories:,}", f"增长均值 {avg_growth:.1f}"),
    ]
    for col, (label, value, note) in zip(st.columns(6), kpis):
        col.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{value}</div>
              <div class="kpi-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_insights(items: list[str]) -> None:
    safe_items = "".join(f"<li>{item}</li>" for item in items[:6])
    st.markdown(
        f"""
        <div class="insight-card">
          <ul>{safe_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def data_mode_label(value: object) -> str:
    labels = {
        "online": "在线",
        "cache": "缓存",
        "sample": "示例",
    }
    return labels.get(str(value), "缓存")


def main() -> None:
    st.set_page_config(
        page_title="AgentPulse - AI Agent 开源生态大屏",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_page_style()

    deps = load_dependencies()
    if deps is None:
        st.warning(GENERIC_ERROR_MESSAGE)
        return

    category_distribution = deps["category_distribution"]
    create_animated_star_trend = deps["create_animated_star_trend"]
    ecosystem_matrix = deps["ecosystem_matrix"]
    generate_insights = deps["generate_insights"]
    growth_score_ranking = deps["growth_score_ranking"]
    health_score_ranking = deps["health_score_ranking"]
    language_distribution = deps["language_distribution"]
    load_repositories = deps["load_repositories"]
    maintenance_pressure_ranking = deps["maintenance_pressure_ranking"]
    read_manifest = deps["read_manifest"]
    repository_summary = deps["repository_summary"]
    update_data_source = deps["update_data_source"]
    write_log = deps["write_log"]

    st.markdown(
        """
        <div class="hero">
          <h1>首页 - AgentPulse 智能体开源生态大屏</h1>
          <a class="repo-link" href="https://github.com/onlynor/agent_pulse" target="_blank" rel="noopener noreferrer" aria-label="GitHub 仓库" title="GitHub 仓库">
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M12 0.5C5.65 0.5 0.5 5.65 0.5 12c0 5.08 3.29 9.39 7.86 10.91 0.58 0.1 0.79-0.25 0.79-0.56 0-0.28-0.01-1.02-0.02-2-3.2 0.7-3.88-1.54-3.88-1.54-0.52-1.33-1.28-1.68-1.28-1.68-1.05-0.72 0.08-0.7 0.08-0.7 1.16 0.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36 0.96 0.1-0.75 0.4-1.25 0.73-1.54-2.55-0.29-5.23-1.28-5.23-5.68 0-1.25 0.45-2.28 1.18-3.08-0.12-0.29-0.51-1.46 0.11-3.04 0 0 0.97-0.31 3.16 1.18 0.92-0.26 1.9-0.38 2.88-0.39 0.98 0 1.96 0.13 2.88 0.39 2.2-1.49 3.16-1.18 3.16-1.18 0.62 1.58 0.23 2.75 0.11 3.04 0.74 0.8 1.18 1.83 1.18 3.08 0 4.42-2.69 5.39-5.25 5.67 0.41 0.36 0.78 1.06 0.78 2.14 0 1.54-0.01 2.79-0.01 3.17 0 0.31 0.21 0.67 0.79 0.56A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35 0.5 12 0.5Z"/>
            </svg>
          </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    manifest = read_manifest()
    source_options = ["本地缓存数据", "在线开源生态数据", "示例数据集"]

    render_sidebar_nav()

    with st.sidebar:
        st.header("数据源")
        source_label = st.selectbox("当前数据源", source_options, index=0)
        update_clicked = st.button("更新当前数据源", type="primary", use_container_width=True)
        st.divider()
        st.header("数据状态")
        st.caption(f"数据模式：{data_mode_label(manifest.get('data_mode', 'cache'))}")
        st.caption(f"仓库数量：{manifest.get('repo_count', 0)}")

    if update_clicked:
        with st.spinner("正在更新当前数据源..."):
            result = update_data_source(source_label)
        if result["ok"] and not result.get("message"):
            st.rerun()
        elif result["ok"]:
            st.warning(str(result.get("message", GENERIC_ERROR_MESSAGE)))
        else:
            st.warning(GENERIC_ERROR_MESSAGE)

    try:
        df = load_repositories()
    except Exception as exc:
        write_log("error", "dashboard_data_load_failed", type(exc).__name__)
        st.warning(GENERIC_ERROR_MESSAGE)
        return

    languages: list[str] = []
    categories: list[str] = []
    keyword = ""
    top_n = 10
    sort_label = "生态评分"

    if not df.empty:
        with st.sidebar:
            st.divider()
            st.header("筛选视图")
            language_options = sorted(df["language"].fillna("未知").unique().tolist())
            category_options = sorted(df["category"].fillna("Other").unique().tolist())
            languages = st.multiselect("主要语言", language_options)
            categories = st.multiselect("项目类别", category_options)
            keyword = st.text_input("搜索仓库", placeholder="输入名称、描述或标签")
            st.divider()
            st.header("排序与展示")
            max_top_n = max(1, min(20, len(df)))
            top_n = st.slider("展示数量", min_value=1, max_value=max_top_n, value=min(10, max_top_n))
            sort_label = st.selectbox(
                "表格排序",
                ["生态评分", "健康评分", "增长评分", "维护压力", "星标数", "更新时间"],
                index=0,
            )

    filtered_df = filter_repositories(df, languages, categories, keyword)
    summary = repository_summary(filtered_df)

    st.markdown('<div class="section-title">生态总览</div>', unsafe_allow_html=True)
    render_kpis(df, filtered_df, summary)

    if df.empty:
        st.info("当前数据源为空，请选择其他数据源。")
        return
    if filtered_df.empty:
        st.warning("当前筛选条件下没有匹配仓库，请调整筛选项。")
        return

    # 添加间距
    st.markdown("<br>", unsafe_allow_html=True)

    # 添加动态星标趋势图
    st.markdown("#### 📈 星标增长趋势动画 (Top 6 高增长仓库)")

    # 显示仓库链接
    if not filtered_df.empty:
        from dynamic_viz import select_trending_repos
        trending = select_trending_repos(filtered_df, top_n=6)
        if not trending.empty:
            links_html = '<div style="margin-bottom: 12px; font-size: 0.9rem; color: #93C5FD;">'
            for idx, (_, repo) in enumerate(trending.iterrows()):
                full_name = repo["full_name"]
                github_url = f"https://github.com/{full_name}"
                stars = int(repo["stargazers_count"])
                links_html += f'<a href="{github_url}" target="_blank" style="color: #38bdf8; text-decoration: none; margin-right: 20px;">🔗 {full_name}</a> <span style="color: #64748B;">({stars:,} ⭐)</span>  '
                if (idx + 1) % 3 == 0:  # 每 3 个换行
                    links_html += '<br>'
            links_html += '</div>'
            st.markdown(links_html, unsafe_allow_html=True)

    st.plotly_chart(create_animated_star_trend(filtered_df, top_n=6), use_container_width=True)

    # 添加间距
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">生态项目矩阵</div>', unsafe_allow_html=True)
    matrix_col, insight_col = st.columns([1.72, 1])
    with matrix_col:
        st.markdown("#### 生态项目矩阵")
        st.plotly_chart(ecosystem_matrix(filtered_df), use_container_width=True)
    with insight_col:
        st.markdown('<div class="section-title">生态洞察</div>', unsafe_allow_html=True)
        render_insights(generate_insights(filtered_df))

    # 添加提示信息
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 查看更多图表分析，请访问左侧导航栏 **📊 细分图表分析** 页面")

    # 移除其他图表，保持主页面简洁


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        safe_write_log("dashboard_unhandled_error", type(exc).__name__)
        st.warning(GENERIC_ERROR_MESSAGE)
