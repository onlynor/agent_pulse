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
    st.markdown(
        """
        <style>
        /* ========== 隐藏右上角 Streamlit 菜单和图标 ========== */
        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        .stDeployButton,
        button[data-testid="stBaseButton-headerNoPadding"],
        button[data-testid="stBaseButton-header"] {
            display: none !important;
            visibility: hidden !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
            pointer-events: none !important;
        }
        header[data-testid="stHeader"] * {
            display: none !important;
            visibility: hidden !important;
        }
        /* 隐藏 Streamlit 内置的运行按钮 */
        section[data-testid="stSidebar"] button[kind="icon"] {display: none !important;}

        /* ========== 自定义导航链接 ========== */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            border: 1px solid rgba(34, 211, 238, 0.20);
            border-radius: 8px;
            color: #e0f2fe !important;
            background: rgba(15, 23, 42, 0.54);
            font-weight: 700;
            margin-bottom: 0.35rem;
            transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            border-color: rgba(34, 211, 238, 0.52);
            color: #22d3ee !important;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.30), rgba(15, 23, 42, 0.92));
            box-shadow: 0 5px 16px rgba(34, 211, 238, 0.16);
            transform: translateY(-1px);
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:active {
            transform: translateY(0) scale(0.98);
            box-shadow: 0 2px 8px rgba(34, 211, 238, 0.12);
        }

        /* ========== 全局页面样式 ========== */
        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(34, 211, 238, 0.16), transparent 26rem),
                linear-gradient(135deg, #020617 0%, #08122d 52%, #020617 100%);
        }
        .block-container {
            padding-top: 0.85rem;
            padding-bottom: 1.6rem;
            max-width: 1520px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #03121d 0%, #071827 50%, #020617 100%);
            border-right: 1px solid rgba(125, 211, 252, 0.34);
        }
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #f8fbff;
        }
        [data-testid="stSidebar"] section {
            padding-top: 0.6rem;
        }
        [data-testid="stSidebar"] hr {
            margin: 0.75rem 0;
            border-color: rgba(125, 211, 252, 0.22);
        }
        [data-testid="stSidebar"] input {
            color: #f8fbff;
            background: rgba(15, 23, 42, 0.96);
        }
        [data-testid="stSidebar"] input::placeholder {
            color: #bae6fd;
            opacity: 0.78;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div {
            background: rgba(15, 23, 42, 0.96);
            border-color: rgba(125, 211, 252, 0.46);
        }
        [data-testid="stSidebar"] .stButton > button {
            color: #f8fbff;
            border: 1px solid rgba(125, 211, 252, 0.68);
            background: linear-gradient(135deg, #0369a1 0%, #0e7490 100%);
            font-weight: 700;
            transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(34, 211, 238, 0.2);
        }
        [data-testid="stSidebar"] .stButton > button:active {
            transform: translateY(0);
        }

        /* ========== Hero 区域 ========== */
        .hero {
            border: 1px solid rgba(34, 211, 238, 0.24);
            border-radius: 8px;
            padding: 14px 18px;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.16), rgba(15, 23, 42, 0.70));
            margin-bottom: 10px;
        }
        .hero h1 {
            margin: 0;
            font-size: 1.85rem;
            letter-spacing: 0;
            color: #e0f2fe;
        }

        /* ========== KPI 卡片 ========== */
        .kpi-card, .insight-card {
            border: 1px solid rgba(34, 211, 238, 0.20);
            border-radius: 8px;
            background: rgba(8, 18, 45, 0.86);
            padding: 13px 14px;
            min-height: 88px;
            transition: all 0.25s ease;
        }
        .kpi-card:hover {
            border-color: rgba(34, 211, 238, 0.40);
            box-shadow: 0 4px 16px rgba(34, 211, 238, 0.12);
            transform: translateY(-2px);
        }
        .kpi-label {
            color: #bfdbfe;
            font-size: 0.82rem;
            margin-bottom: 7px;
        }
        .kpi-value {
            color: #e0f2fe;
            font-size: 1.45rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .kpi-note {
            color: #38bdf8;
            font-size: 0.76rem;
            margin-top: 7px;
        }

        /* ========== Section 标题 ========== */
        .section-title {
            font-size: 1.02rem;
            font-weight: 700;
            color: #e0f2fe;
            margin: 0.45rem 0 0.55rem;
        }

        /* ========== Insight 卡片 ========== */
        .insight-card ul {
            margin: 0;
            padding-left: 1.1rem;
        }
        .insight-card li {
            color: #dbeafe;
            margin-bottom: 0.55rem;
            line-height: 1.45;
        }
        .insight-card:hover {
            border-color: rgba(34, 211, 238, 0.40);
            box-shadow: 0 4px 16px rgba(34, 211, 238, 0.12);
        }

        /* ========== DataFrame ========== */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(34, 211, 238, 0.18);
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_time(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    return text.replace("T", " ").replace("Z", "")


def render_sidebar_nav() -> None:
    """Render explicit navigation labels instead of Streamlit's default file names."""
    with st.sidebar:
        st.page_link("app.py", label="首页", icon="🏠")
        st.page_link("pages/2_📊_细分图表分析.py", label="细分图表分析", icon="📊")
        st.page_link("pages/3_📋_原始数据.py", label="原始数据", icon="📋")
        st.link_button("GitHub: onlynor", "https://github.com/onlynor", use_container_width=True)
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
        page_icon="♛",
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
          <h1>🏠 首页 - AgentPulse 智能体开源生态大屏</h1>
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
        st.caption(f"最近更新时间：{format_time(manifest.get('last_updated_at', '')) or '暂无'}")

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
