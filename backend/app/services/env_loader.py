from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_env_path(env_path: str | Path | None = None) -> Path:
    if env_path is not None:
        return Path(env_path).resolve()
    return get_project_root() / ".env"


def load_project_env(env_path: str | Path | None = None, *, override: bool = True) -> Path:
    resolved_env_path = get_env_path(env_path)
    if not resolved_env_path.exists():
        raise FileNotFoundError(f"未找到 .env 文件: {resolved_env_path}")
    load_dotenv(dotenv_path=resolved_env_path, override=override)
    return resolved_env_path


def get_required_env(name: str, env_path: str | Path | None = None) -> str:
    load_project_env(env_path)
    value = os.getenv(name, "").strip()
    if not value:
        env_file = get_env_path(env_path)
        raise ValueError(f"未在 {env_file} 中设置环境变量: {name}")
    return value
