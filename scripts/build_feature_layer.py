from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.data_registry import DatasetPathResolver
from backend.app.services.result_writer import write_json


DATASET_MAPPING = {
    "01_token_candidate_pool": "token_overview_daily",
    "02_token_cost_basis": "address_feature_snapshot",
    "03_token_position_validation": "address_feature_timeline",
    "04_token_pnl_snapshot": "token_pnl_distribution",
}
PATH_RESOLVER = DatasetPathResolver(PROJECT_ROOT)


def normalize_dune_payload(payload: dict, *, dataset_name: str, token_symbol: str) -> dict:
    result = payload.get("result", {}) if isinstance(payload, dict) else {}
    rows = result.get("rows", []) if isinstance(result, dict) else []
    return {
        "dataset_name": dataset_name,
        "token_symbol": token_symbol,
        "query_id": payload.get("query_id"),
        "execution_id": payload.get("execution_id"),
        "state": payload.get("state"),
        "row_count": len(rows),
        "rows": rows,
    }


def main() -> None:
    raw_root = PATH_RESOLVER.resolve_raw_dune_root()

    for token_dir in raw_root.glob("*"):
        if not token_dir.is_dir():
            continue

        token_symbol = token_dir.name
        for raw_file in token_dir.glob("*.json"):
            dataset_name = DATASET_MAPPING.get(raw_file.stem)
            if not dataset_name:
                continue

            with raw_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)

            normalized_payload = normalize_dune_payload(
                payload,
                dataset_name=dataset_name,
                token_symbol=token_symbol,
            )
            output_path = PATH_RESOLVER.resolve_path(dataset_name, token_symbol)
            write_json(normalized_payload, output_path)
            print(f"已生成特征层文件: {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
