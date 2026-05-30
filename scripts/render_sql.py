from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.config_loader import load_project_config
from backend.app.services.sql_renderer import SQLRenderer


def main() -> None:
    config = load_project_config(PROJECT_ROOT / "config" / "tokens.json")
    renderer = SQLRenderer(project_root=PROJECT_ROOT)
    rendered_files = renderer.render_all(config)

    print("SQL 渲染完成:")
    for file_path in rendered_files:
        print(f"- {file_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
