from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DatasetNotFoundError(FileNotFoundError):
    """Raised when a required dataset file is missing."""


class DatasetInvalidError(ValueError):
    """Raised when a dataset file exists but has unexpected structure."""


class FeatureStoreRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def read_processed_dataset(self, dataset_name: str, token_symbol: str) -> dict[str, Any]:
        path = self.project_root / "data" / "processed" / dataset_name / f"{token_symbol}.json"
        return self._read_dataset(path, token_symbol)

    def read_feature_dataset(self, dataset_name: str, token_symbol: str) -> dict[str, Any]:
        path = self.project_root / "data" / "features" / dataset_name / f"{token_symbol}.json"
        return self._read_dataset(path, token_symbol)

    def _read_dataset(self, path: Path, token_symbol: str) -> dict[str, Any]:
        if not path.exists():
            raise DatasetNotFoundError(f"未找到数据文件: {path}")

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise DatasetInvalidError(f"数据文件结构无效: {path}")

        payload_token = str(payload.get("token_symbol", "")).upper()
        if payload_token != token_symbol.upper():
            raise DatasetInvalidError(
                f"数据文件 token 不匹配: {payload_token or 'EMPTY'} != {token_symbol.upper()}"
            )
        return payload
