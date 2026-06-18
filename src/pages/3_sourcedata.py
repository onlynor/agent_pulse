"""AgentPulse - 原始数据与 GitHub 链接页面"""
import streamlit as st

# 必须第一个调用
st.set_page_config(
    page_title="原始数据 - AgentPulse",
    layout="wide",
)

import sys
from pathlib import Path

    # 添加源码目录到导入路径
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

try:
    from database import load_repositories
    from app import apply_page_style, render_page_hero, render_sidebar_nav
except ImportError:
    st.error("无法加载模块，请确保在正确的目录运行应用。")
    st.stop()


def main():
    apply_page_style()
    render_sidebar_nav()

    render_page_hero("原始数据与 GitHub 链接")

    try:
        df = load_repositories()
    except Exception:
        st.error("加载数据失败")
        return

    if df.empty:
        st.info("暂无项目数据")
        return

    # 按类别分组
    categories = sorted(df["category"].fillna("Other").unique())

    st.markdown("### 📊 项目总览")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("项目总数", f"{len(df):,}")
    with col2:
        st.metric("类别数量", len(categories))
    with col3:
        total_stars = int(df["stargazers_count"].sum())
        st.metric("总星标数", f"{total_stars:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 类别筛选
    selected_category = st.selectbox(
        "选择类别查看项目",
        ["全部"] + categories,
        index=0,
    )

    if selected_category != "全部":
        df_display = df[df["category"] == selected_category]
    else:
        df_display = df

    # 排序选项
    sort_by = st.selectbox(
        "排序方式",
        ["星标数", "派生数", "健康评分", "增长评分", "更新时间"],
        index=0,
    )

    sort_map = {
        "星标数": "stargazers_count",
        "派生数": "forks_count",
        "健康评分": "health_score",
        "增长评分": "growth_score",
        "更新时间": "updated_at",
    }

    df_display = df_display.sort_values(sort_map[sort_by], ascending=False)

    st.markdown(f"### 🔗 项目列表 ({len(df_display)} 个项目)")

    # 显示项目卡片
    for idx, (_, repo) in enumerate(df_display.iterrows()):
        with st.expander(
            f"**{repo['full_name']}** - ⭐ {repo['stargazers_count']:,} | 🍴 {repo['forks_count']:,}",
            expanded=False,
        ):
            col_info, col_stats = st.columns([2, 1])

            with col_info:
                st.markdown(f"**描述**: {repo['description'] or '暂无描述'}")
                st.markdown(f"**语言**: {repo['language'] or '未知'}")
                st.markdown(f"**类别**: {repo['category']}")
                st.markdown(f"**许可证**: {repo.get('license', '未知')}")

                # GitHub 链接
                github_url = f"https://github.com/{repo['full_name']}"
                st.link_button("🔗 访问 GitHub", github_url)

                # 主页链接
                if repo.get("homepage"):
                    st.link_button("🏠 项目主页", repo["homepage"])

            with col_stats:
                st.markdown("**📊 统计数据**")
                st.markdown(f"- 健康评分: {repo.get('health_score', 0):.1f}")
                st.markdown(f"- 增长评分: {repo.get('growth_score', 0):.1f}")
                st.markdown(f"- 生态评分: {repo.get('ecosystem_score', 0):.1f}")
                st.markdown(f"- 开放问题: {repo['open_issues_count']:,}")
                st.markdown(f"- 观察者: {repo.get('watchers_count', 0):,}")

            # 主题标签
            if repo.get("topics"):
                topics = repo["topics"]
                if isinstance(topics, str):
                    topics = [topic.strip() for topic in topics.split(",") if topic.strip()]
                if topics:
                    topics_html = " ".join([
                        f'<span style="background: rgba(59, 130, 246, 0.2); color: #38bdf8; '
                        f'padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; '
                        f'margin-right: 6px;">{topic}</span>'
                        for topic in topics[:10]
                    ])
                    st.markdown(f"**标签**: {topics_html}", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
