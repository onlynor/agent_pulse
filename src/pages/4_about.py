"""AgentPulse - 项目说明页面"""
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="项目说明 - AgentPulse",
    layout="wide",
)

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

try:
    from app import apply_page_style, data_mode_label, render_sidebar_nav
    from data_store import read_manifest
    from database import load_repositories
except ImportError:
    st.error("无法加载模块，请确保在正确的目录运行应用。")
    st.stop()


def render_metric(label: str, value: str, note: str) -> str:
    return (
        '<div class="about-metric">'
        f'<div class="about-metric-label">{label}</div>'
        f'<div class="about-metric-value">{value}</div>'
        f'<div class="about-metric-note">{note}</div>'
        "</div>"
    )


def main() -> None:
    apply_page_style()
    render_sidebar_nav()

    manifest = read_manifest()
    try:
        df = load_repositories()
    except Exception:
        df = None

    repo_count = int(manifest.get("repo_count", 0) or 0)
    data_mode = data_mode_label(manifest.get("data_mode", "cache"))
    source = str(manifest.get("active_source", "本地缓存数据"))
    categories = 0 if df is None or df.empty else int(df["category"].nunique())
    languages = 0 if df is None or df.empty else int(df["language"].nunique())

    metrics_html = "".join(
        [
            render_metric("数据源", source, "当前页面使用的数据来源"),
            render_metric("仓库数量", f"{repo_count:,}", "manifest 中记录的项目数量"),
            render_metric("数据模式", data_mode, "缓存、在线或示例数据"),
            render_metric("分类 / 语言", f"{categories} / {languages}", "当前数据集覆盖范围"),
        ]
    )

    html = f"""
        <div class="hero">
          <h1>项目说明 - AgentPulse</h1>
        </div>

        <div class="about-page">
          <section class="about-intro">
            <h2>这个项目做什么</h2>
            <p>
              AgentPulse 是一个 AI Agent 开源生态分析面板。应用读取本地仓库数据，
              计算项目评分，并通过图表、排行榜和明细列表展示仓库热度、活跃度、
              维护压力与技术分布。
            </p>
          </section>

          <section class="about-section">
            <h2>当前数据概览</h2>
            <div class="about-metrics">{metrics_html}</div>
          </section>

          <div class="about-grid">
            <section class="about-section">
              <h2>页面结构</h2>
              <div class="about-flow">
                <div><strong>首页</strong><span>生态总览、核心指标、趋势动画、项目矩阵。</span></div>
                <div><strong>细分图表分析</strong><span>健康评分、增长潜力、类别分布、语言分布、维护压力。</span></div>
                <div><strong>原始数据</strong><span>项目列表、仓库基础信息、GitHub 链接和项目主页。</span></div>
                <div><strong>项目说明</strong><span>说明项目用途、数据链路、技术栈和页面组成。</span></div>
              </div>
            </section>

            <section class="about-section">
              <h2>数据链路</h2>
              <div class="about-flow">
                <div><strong>读取</strong><span>从本地 CSV、配置 JSON 和 manifest 加载数据。</span></div>
                <div><strong>整理</strong><span>统一仓库字段，处理语言、类别、星标、Fork、Issue、时间等信息。</span></div>
                <div><strong>评分</strong><span>计算健康评分、增长评分、生态评分和维护压力。</span></div>
                <div><strong>展示</strong><span>通过 Streamlit 页面和 Plotly 图表输出分析结果。</span></div>
              </div>
            </section>
          </div>

          <section class="about-section">
            <h2>技术栈</h2>
            <div class="tech-list">
              <div class="tech-item"><strong>Python</strong><span>应用主体、数据处理和评分逻辑。</span></div>
              <div class="tech-item"><strong>Streamlit</strong><span>多页面界面、侧栏导航和交互控件。</span></div>
              <div class="tech-item"><strong>Pandas</strong><span>CSV 读取、筛选、排序和指标聚合。</span></div>
              <div class="tech-item"><strong>Plotly</strong><span>趋势动画、排行榜、分布图和矩阵图。</span></div>
              <div class="tech-item"><strong>CSV / JSON</strong><span>本地缓存数据、数据源配置和状态记录。</span></div>
              <div class="tech-item"><strong>Docker</strong><span>容器化运行配置。</span></div>
            </div>
          </section>
        </div>
        """.strip()
    st.html(html)


if __name__ == "__main__":
    main()
