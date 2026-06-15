from pathlib import Path
from datetime import datetime, timezone
import os
import re

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
DATABASE_DIR = OUTPUT_DIR / "database"
LOGS_DIR = OUTPUT_DIR / "logs"
MANIFEST_FILE = DATA_DIR / "manifest.json"
SOURCES_DIR = DATA_DIR / "sources"
ONLINE_SOURCE_FILE = SOURCES_DIR / "online_ecosystem.json"
SAMPLE_SOURCE_FILE = SOURCES_DIR / "sample_repos.json"
CACHE_DIR = DATA_DIR / "cache"
LEGACY_DIR = DATA_DIR / "legacy"
REPOS_FILE = SOURCES_DIR / "repos.json"
SEED_DATA_FILE = LEGACY_DIR / "repositories_seed.json"
RAW_DIR = CACHE_DIR
RAW_REPOS_DIR = LEGACY_DIR / "repos"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DERIVED_DIR = DATA_DIR / "derived"
DATABASE_PATH = DATABASE_DIR / "agent_pulse.db"
LOG_FILE = LOGS_DIR / "agent_pulse.log"
GENERIC_ERROR_MESSAGE = "数据加载失败，请点击刷新按钮重试"
ONLINE_FALLBACK_MESSAGE = "当前在线数据暂时不可用，已切换到本地缓存"
EMPTY_SOURCE_MESSAGE = "当前数据源为空，请选择其他数据源"
DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_MAX_REPOS = 300

V2_DATA_DIRS = [
    DATA_DIR,
    SOURCES_DIR,
    CACHE_DIR,
]


def load_settings() -> dict:
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "github_token": os.getenv("GITHUB_TOKEN", "").strip(),
        "github_api_base_url": os.getenv(
            "GITHUB_API_BASE_URL", "https://api.github.com"
        ).rstrip("/"),
    }


def ensure_database_directory() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_log_directory() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_data_directories() -> None:
    for directory in V2_DATA_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def sanitize_log_text(value: object) -> str:
    text = str(value)
    text = re.sub(r"[A-Za-z]:\\[^\s]+", "[本地路径]", text)
    text = re.sub(r"/(?:home|Users|tmp|var|workspace|mnt)/[^\s]+", "[本地路径]", text)
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:500]


def write_log(level: str, event: str, detail: object = "") -> None:
    try:
        ensure_log_directory()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        safe_level = sanitize_log_text(level.upper())
        safe_event = sanitize_log_text(event)
        safe_detail = sanitize_log_text(detail)
        line = f"{timestamp} | {safe_level} | {safe_event} | {safe_detail}\n"
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(line)
    except OSError:
        pass
