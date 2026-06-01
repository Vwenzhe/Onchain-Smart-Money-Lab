from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.services.data_registry import DatasetPathResolver


class DatasetNotFoundError(FileNotFoundError):
    """Raised when a required dataset file is missing."""


class DatasetInvalidError(ValueError):
    """Raised when a dataset file exists but has unexpected structure."""


class FeatureStoreRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.path_resolver = DatasetPathResolver(self.project_root)

    def read_processed_dataset(self, dataset_name: str, token_symbol: str) -> dict[str, Any]:
        path = self.path_resolver.resolve_path(dataset_name, token_symbol)
        return self._read_dataset(path, token_symbol)

    def read_feature_dataset(self, dataset_name: str, token_symbol: str) -> dict[str, Any]:
        path = self.path_resolver.resolve_path(dataset_name, token_symbol)
        return self._read_dataset(path, token_symbol)

    def read_global_feature_dataset(self, dataset_name: str) -> dict[str, Any]:
        path = self.path_resolver.resolve_path(dataset_name)
        return self._read_dataset(path, token_symbol=None)

    def _read_dataset(self, path: Path, token_symbol: str | None) -> dict[str, Any]:
        if not path.exists():
            raise DatasetNotFoundError(f"未找到数据文件: {path}")

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise DatasetInvalidError(f"数据文件结构无效: {path}")

        if token_symbol is not None:
            payload_token = str(payload.get("token_symbol", "")).upper()
            if payload_token != token_symbol.upper():
                raise DatasetInvalidError(
                    f"数据文件 token 不匹配: {payload_token or 'EMPTY'} != {token_symbol.upper()}"
                )
        return payload
