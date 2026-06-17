"""AgentPulse - 细分图表分析页面"""
import streamlit as st

st.set_page_config(
    page_title="细分图表分析 - AgentPulse",
    layout="wide",
)

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

try:
    from database import load_repositories
    from app import apply_page_style, filter_repositories, make_display_table, render_sidebar_nav
    from charts import (
        language_distribution,
        category_distribution,
        health_score_ranking,
        growth_score_ranking,
        maintenance_pressure_ranking,
    )
except ImportError as e:
    st.error(f"无法加载模块: {e}")
    st.stop()


def main():
    apply_page_style()
    render_sidebar_nav()

    st.markdown(
        '<div class="hero"><h1>📊 细分图表分析</h1></div>',
        unsafe_allow_html=True,
    )

    try:
        df = load_repositories()
    except Exception:
        st.error("加载数据失败")
        return

    if df.empty:
        st.info("暂无数据")
        return

    with st.sidebar:
        st.header("筛选选项")
        language_options = sorted(df["language"].fillna("未知").unique().tolist())
        category_options = sorted(df["category"].fillna("Other").unique().tolist())
        languages = st.multiselect("主要语言", language_options)
        categories = st.multiselect("项目类别", category_options)
        keyword = st.text_input("搜索仓库", placeholder="输入名称、描述或标签")

        st.divider()
        st.header("展示选项")
        top_n = st.slider("榜单数量", min_value=5, max_value=20, value=10)

    filtered_df = filter_repositories(df, languages, categories, keyword)

    if filtered_df.empty:
        st.warning("当前筛选条件下没有匹配仓库，请调整筛选项。")
        return

    # 排行榜部分
    st.markdown("### 🏆 排行榜分析")
    health_col, growth_col = st.columns(2)
    with health_col:
        st.markdown("#### 项目健康评分榜")
        st.plotly_chart(health_score_ranking(filtered_df, top_n), use_container_width=True)

    with growth_col:
        st.markdown("#### 增长潜力榜")
        st.plotly_chart(growth_score_ranking(filtered_df, top_n), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 分布图部分
    st.markdown("### 📈 分布分析")
    category_col, language_col = st.columns(2)
    with category_col:
        st.markdown("#### 项目类别分布")
        st.plotly_chart(category_distribution(filtered_df), use_container_width=True)

    with language_col:
        st.markdown("#### 技术栈语言分布 (Top 10)")
        st.plotly_chart(language_distribution(filtered_df), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 维护压力与明细表
    st.markdown("### ⚠️ 维护分析与项目明细")
    pressure_col, table_col = st.columns([1, 1.25])

    with pressure_col:
        st.markdown("#### 维护压力榜")
        st.plotly_chart(maintenance_pressure_ranking(filtered_df, top_n), use_container_width=True)

    with table_col:
        st.markdown("#### 项目明细表")
        sort_by = st.selectbox(
            "排序方式",
            ["生态评分", "健康评分", "增长评分", "维护压力", "星标数", "更新时间"],
            index=0,
        )
        sort_map = {
            "生态评分": "ecosystem_score",
            "健康评分": "health_score",
            "增长评分": "growth_score",
            "维护压力": "maintenance_pressure",
            "星标数": "stargazers_count",
            "更新时间": "updated_at",
        }
        sorted_df = filtered_df.sort_values(sort_map[sort_by], ascending=False)
        st.dataframe(make_display_table(sorted_df), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
