# AgentPulse

AgentPulse 是一个 AI Agent 开源生态分析面板，用来观察热门 Agent 项目的活跃度、影响力和维护状态。

它内置了一份可直接运行的本地数据集，不需要 GitHub Token 也能打开页面查看分析结果。

在线访问：https://visboard.streamlit.app/

## 你可以看到什么

- AI Agent 开源项目整体规模和热度
- 星标、Fork、Issue、健康评分等核心指标
- 近 12 个月星标增长趋势动画
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

## 页面

- 首页：生态总览、趋势动画、项目矩阵和生态洞察
- 细分图表分析：排行、分布、维护压力和项目明细
- 原始数据：项目列表、仓库信息和 GitHub 链接
- 项目说明：项目用途、数据链路、技术栈和页面组成

## 依赖

- Python 3.11+
- Streamlit
- Pandas
- Plotly
- Requests

## License

MIT
