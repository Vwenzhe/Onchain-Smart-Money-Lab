from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.repositories.feature_store_repository import (
    DatasetInvalidError,
    DatasetNotFoundError,
    FeatureStoreRepository,
)
from backend.app.services.config_loader import load_project_config

REQUIRED_PROCESSED_DATASETS = (
    "token_overview_daily",
    "address_feature_snapshot",
    "address_feature_timeline",
    "token_pnl_distribution",
)
REQUIRED_FEATURE_DATASETS = (
    "address_profiles",
    "token_ai_summary",
)
TOKEN_AI_SUMMARY_FIELDS = (
    "trend_summary",
    "market_context",
    "event_attribution",
    "risk_warning",
    "confidence",
)


class WorkflowValidationError(RuntimeError):
    """Raised when required workflow artifacts are missing or invalid."""


def validate_outputs() -> None:
    repository = FeatureStoreRepository(PROJECT_ROOT)
    config = load_project_config(PROJECT_ROOT / "config" / "tokens.json")
    enabled_tokens = [token.token_symbol.upper() for token in config.tokens]

    for token_symbol in enabled_tokens:
        for dataset_key in REQUIRED_PROCESSED_DATASETS:
            payload = repository.read_processed_dataset(dataset_key, token_symbol)
            _validate_rows_payload(payload, dataset_key=dataset_key, token_symbol=token_symbol)

        profiles = repository.read_feature_dataset("address_profiles", token_symbol)
        _validate_rows_payload(profiles, dataset_key="address_profiles", token_symbol=token_symbol)

        ai_summary = repository.read_feature_dataset("token_ai_summary", token_symbol)
        _validate_token_ai_summary(ai_summary, token_symbol=token_symbol)

    prices_latest = repository.read_global_feature_dataset("token_prices_latest")
    _validate_latest_prices(prices_latest, enabled_tokens)


def _validate_rows_payload(payload: dict[str, Any], *, dataset_key: str, token_symbol: str) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise WorkflowValidationError(f"{dataset_key}/{token_symbol} 缺少 rows 列表")

    row_count = payload.get("row_count")
    if row_count is not None and int(row_count) != len(rows):
        raise WorkflowValidationError(
            f"{dataset_key}/{token_symbol} 的 row_count={row_count} 与 rows 数量={len(rows)} 不一致"
        )

    if not rows:
        raise WorkflowValidationError(f"{dataset_key}/{token_symbol} 未生成任何记录")


def _validate_token_ai_summary(payload: dict[str, Any], *, token_symbol: str) -> None:
    analysis = payload.get("analysis")
    if not isinstance(analysis, dict):
        raise WorkflowValidationError(f"token_ai_summary/{token_symbol} 缺少 analysis")

    missing_fields = [field for field in TOKEN_AI_SUMMARY_FIELDS if not str(analysis.get(field, "")).strip()]
    if missing_fields:
        raise WorkflowValidationError(
            f"token_ai_summary/{token_symbol} 缺少字段: {', '.join(missing_fields)}"
        )


def _validate_latest_prices(payload: dict[str, Any], enabled_tokens: list[str]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise WorkflowValidationError("token_prices_latest 缺少价格 rows")

    actual_tokens = {str(row.get("token_symbol", "")).upper() for row in rows}
    missing_tokens = [token for token in enabled_tokens if token not in actual_tokens]
    if missing_tokens:
        raise WorkflowValidationError(
            f"token_prices_latest 缺少价格快照: {', '.join(missing_tokens)}"
        )


def main() -> None:
    try:
        validate_outputs()
    except (DatasetNotFoundError, DatasetInvalidError, WorkflowValidationError) as exc:
        raise SystemExit(f"工作流产物校验失败: {exc}") from exc

    print("工作流产物校验通过。")


if __name__ == "__main__":
    main()
