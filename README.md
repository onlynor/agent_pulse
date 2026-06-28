# AgentPulse

AgentPulse 是一个 AI Agent 开源生态分析面板，用来观察热门 Agent 项目的活跃度、影响力和维护状态。

它内置了一份可直接运行的本地数据集，不需要 GitHub Token 也能打开页面查看分析结果。

在线访问：https://visboard.streamlit.app/

## 你可以看到什么

- AI Agent 开源项目整体规模和热度
- 星标、Fork、Issue、健康评分等核心指标
- 已采集项目 Top 15 星标数排名动画
- 项目影响力与活跃度矩阵
- 技术栈语言分布和项目类别分布
- 增长潜力、健康评分、维护压力排行榜
- 每个项目的基础信息和 GitHub 跳转链接

## 运行

推荐使用 uv：

```powershell
uv run streamlit run src/app.py
```

或使用 pip：

```powershell
pip install -r requirements.txt
streamlit run src/app.py
```

打开浏览器访问：

```text
http://localhost:8501
```

## Docker

```powershell
docker build -t agent-pulse .
docker run --rm -p 8501:8501 agent-pulse
```

然后访问：

```text
http://localhost:8501
```

## 数据

项目默认使用内置本地数据，因此可以离线启动。

如果配置 `GITHUB_TOKEN`，页面中的在线数据源可以从 GitHub API 更新最新仓库数据；没有 Token 时，应用会继续使用本地缓存数据。

在线生态数据会优先补齐配置中的重点仓库，例如 OpenClaw、Hermes Agent、opencode 等，避免热门项目因搜索结果波动缺失。

## 项目结构图

**图 1 AgentPulse Git 仓库项目结构**

```text
agent_pulse/
├── data/                  # 本地数据与缓存配置
│   ├── cache/             # CSV 仓库缓存
│   └── sources/           # 在线与示例数据源配置
├── src/                   # 系统核心代码
│   ├── app.py             # Streamlit 首页入口
│   ├── pages/             # 细分图表、原始数据、项目说明页面
│   ├── collect_data.py    # GitHub 数据采集
│   ├── data_store.py      # 数据集读写与派生文件生成
│   ├── database.py        # SQLite 数据访问
│   ├── transform.py       # 数据清洗、标准化与字段整理
│   ├── scoring.py         # 指标评分计算
│   └── charts.py          # Plotly 可视化图表生成
├── .streamlit/            # Streamlit 运行配置
├── requirements.txt       # Python 依赖列表
├── Dockerfile             # 容器化部署配置
└── README.md              # 项目说明文档
```

## 页面

- 首页：生态总览、Top 15 星标排行动画、项目矩阵和生态洞察
- 细分图表分析：排行、分布、维护压力和项目明细
- 原始数据：项目列表、仓库信息和 GitHub 链接
- 项目说明：项目用途、数据链路、技术栈和页面组成

## 开发说明

- 当前界面保持固定暗色大屏风格，不启用运行时亮暗主题切换。
- `scripts/` 为本地辅助脚本目录，已在 `.gitignore` 中忽略，不作为应用运行依赖。

## 依赖

- Python 3.11+
- Streamlit
- Pandas
- Plotly
- Requests

## License

MIT
