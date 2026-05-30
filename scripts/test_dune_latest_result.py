from __future__ import annotations

import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.dune_client import DuneClient
from backend.app.services.env_loader import load_project_env


def main() -> None:
    env_path = load_project_env(PROJECT_ROOT / ".env")

    query_id = int(os.getenv("DUNE_TEST_QUERY_ID", "7607523"))
    output_dir = PROJECT_ROOT / "data" / "raw" / "dune" / "manual_test"

    client = DuneClient(env_path=env_path)
    saved_path = client.save_latest_result(
        query_id=query_id,
        raw_output_dir=output_dir,
        output_name=f"query_{query_id}_latest.json",
    )

    print(f"已保存 Dune 最新结果: {saved_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
