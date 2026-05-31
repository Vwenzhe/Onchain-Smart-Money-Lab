from __future__ import annotations

from pathlib import Path


def load_prompt_text(project_root: str | Path, relative_path: str) -> str:
    path = Path(project_root).resolve() / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
