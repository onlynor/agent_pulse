from __future__ import annotations

import pandas as pd


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Workflow Automation", ("workflow", "automation", "n8n", "flowise", "low-code", "no-code")),
    ("Coding Agent", ("coding", "code", "software", "developer", "devtool", "interpreter", "gpt-engineer", "openhands")),
    ("MCP Ecosystem", ("mcp", "model-context-protocol")),
    ("RAG Platform", ("rag", "retrieval", "knowledge", "vector")),
    ("Multi-Agent System", ("multi-agent", "multiagent", "agent society", "collaboration", "chatdev", "metagpt")),
    ("UI / WebUI", ("webui", "web-ui", " visual ", " interface ")),
    ("LLM App Framework", ("llm app", "llm-framework", "application", "langchain", "semantic-kernel")),
    ("DevTool Agent", ("cli", "tool", "developer-tools", "sandbox", "browser")),
    ("Agent Framework", ("agent", "agents", "agentic", "autonomous", "assistant")),
]


def classify_repository(row: pd.Series) -> str:
    text = " ".join(
        [
            str(row.get("name", "")),
            str(row.get("description", "")),
            str(row.get("topics", "")),
        ]
    ).lower()
    padded_text = f" {text.replace(',', ' ')} "
    for category, keywords in CATEGORY_RULES:
        if any(keyword in padded_text or keyword in text for keyword in keywords):
            return category
    return "Other"


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["category"] = []
        return df

    result = df.copy()
    result["category"] = result.apply(classify_repository, axis=1)
    return result
