from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class DatasetResolutionError(ValueError):
    """Raised when a dataset key cannot be resolved to a storage location."""


@dataclass(frozen=True)
class DatasetSpec:
    dataset_key: str
    storage_scope: str
    relative_dir: str
    token_scoped: bool = True
    filename_template: str = "{token_symbol}.json"


DATASET_SPECS: dict[str, DatasetSpec] = {
    "token_overview_daily": DatasetSpec(
        dataset_key="token_overview_daily",
        storage_scope="processed",
        relative_dir="token_overview_daily",
    ),
    "address_feature_snapshot": DatasetSpec(
        dataset_key="address_feature_snapshot",
        storage_scope="processed",
        relative_dir="address_feature_snapshot",
    ),
    "address_feature_timeline": DatasetSpec(
        dataset_key="address_feature_timeline",
        storage_scope="processed",
        relative_dir="address_feature_timeline",
    ),
    "token_pnl_distribution": DatasetSpec(
        dataset_key="token_pnl_distribution",
        storage_scope="processed",
        relative_dir="token_pnl_distribution",
    ),
    "address_profiles": DatasetSpec(
        dataset_key="address_profiles",
        storage_scope="features",
        relative_dir="address_profiles",
    ),
    "token_ai_summary": DatasetSpec(
        dataset_key="token_ai_summary",
        storage_scope="features",
        relative_dir="token_ai_summary",
    ),
    "token_prices_latest": DatasetSpec(
        dataset_key="token_prices_latest",
        storage_scope="features",
        relative_dir="token_prices",
        token_scoped=False,
        filename_template="latest.json",
    ),
    "token_prices_history": DatasetSpec(
        dataset_key="token_prices_history",
        storage_scope="features",
        relative_dir="token_prices/history",
    ),
}


class DatasetPathResolver:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def resolve_path(self, dataset_key: str, token_symbol: str | None = None) -> Path:
        spec = self.get_spec(dataset_key)
        relative_path = Path("data") / spec.storage_scope / spec.relative_dir / self._build_filename(
            spec, token_symbol
        )
        return self.project_root / relative_path

    def build_reference(self, dataset_key: str, token_symbol: str | None = None) -> dict[str, str | None]:
        spec = self.get_spec(dataset_key)
        normalized_token = self._normalize_token(token_symbol) if token_symbol else None
        if spec.token_scoped and normalized_token is None:
            raise DatasetResolutionError(f"数据集 {dataset_key} 需要 token_symbol")
        return {
            "dataset_key": spec.dataset_key,
            "storage_scope": spec.storage_scope,
            "token_symbol": normalized_token,
        }

    def resolve_raw_dune_root(self) -> Path:
        return self.project_root / "data" / "raw" / "dune"

    def resolve_raw_dune_token_dir(self, token_symbol: str) -> Path:
        return self.resolve_raw_dune_root() / self._normalize_token(token_symbol)

    def get_spec(self, dataset_key: str) -> DatasetSpec:
        spec = DATASET_SPECS.get(dataset_key)
        if spec is None:
            raise DatasetResolutionError(f"未注册的数据集标识: {dataset_key}")
        return spec

    def _build_filename(self, spec: DatasetSpec, token_symbol: str | None) -> str:
        if spec.token_scoped:
            normalized_token = self._normalize_token(token_symbol)
            return spec.filename_template.format(token_symbol=normalized_token)
        return spec.filename_template

    def _normalize_token(self, token_symbol: str | None) -> str:
        if token_symbol is None or not token_symbol.strip():
            raise DatasetResolutionError("token_symbol 不能为空")
        return token_symbol.strip().upper()
