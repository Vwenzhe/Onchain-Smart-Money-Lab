from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.data_registry import DatasetPathResolver
from backend.app.services.coingecko_client import CoinGeckoClient
from backend.app.services.result_writer import write_json

CONFIG_PATH = PROJECT_ROOT / "config" / "token_prices.json"
PATH_RESOLVER = DatasetPathResolver(PROJECT_ROOT)
LATEST_OUTPUT_PATH = PATH_RESOLVER.resolve_path("token_prices_latest")


def load_price_config(config_path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到价格配置文件: {path}")
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not payload.get("assets"):
        raise ValueError("价格配置中未定义任何资产")
    return payload


def fetch_price_snapshots(config_path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    config = load_price_config(config_path)
    client = CoinGeckoClient()
    queried_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    vs_currency = str(config.get("vs_currency", "usd"))

    assets = list(config["assets"])
    coin_assets = [asset for asset in assets if asset["lookup_type"] == "coin_id"]
    contract_assets = [asset for asset in assets if asset["lookup_type"] == "contract_address"]

    price_rows: list[dict[str, Any]] = []

    if coin_assets:
        price_by_id = client.get_prices_by_ids(
            [str(asset["coin_id"]) for asset in coin_assets],
            vs_currency=vs_currency,
        )
        for asset in coin_assets:
            coin_id = str(asset["coin_id"])
            payload = price_by_id.get(coin_id, {})
            price_rows.append(
                build_price_row(
                    asset=asset,
                    payload=payload,
                    queried_at=queried_at,
                    vs_currency=vs_currency,
                    source_key=coin_id,
                )
            )

    contracts_by_platform: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for asset in contract_assets:
        contracts_by_platform[str(asset["asset_platform_id"])].append(asset)

    for platform_id, platform_assets in contracts_by_platform.items():
        contract_response = client.get_prices_by_contracts(
            platform_id,
            [str(asset["contract_address"]) for asset in platform_assets],
            vs_currency=vs_currency,
        )
        for asset in platform_assets:
            address = str(asset["contract_address"]).lower()
            payload = contract_response.get(address, {})
            price_rows.append(
                build_price_row(
                    asset=asset,
                    payload=payload,
                    queried_at=queried_at,
                    vs_currency=vs_currency,
                    source_key=address,
                )
            )

    latest_payload = {
        "dataset_name": "token_price_latest_snapshot",
        "source": "coingecko",
        "vs_currency": vs_currency,
        "interval_minutes": int(config.get("interval_minutes", 30)),
        "generated_at": queried_at,
        "row_count": len(price_rows),
        "rows": price_rows,
    }
    write_json(latest_payload, LATEST_OUTPUT_PATH)

    for row in price_rows:
        update_history(row=row, interval_minutes=int(config.get("interval_minutes", 30)))

    return latest_payload


def build_price_row(
    *,
    asset: dict[str, Any],
    payload: dict[str, Any],
    queried_at: str,
    vs_currency: str,
    source_key: str,
) -> dict[str, Any]:
    if not payload:
        raise ValueError(f"CoinGecko 未返回价格数据: {asset['token_symbol']} ({source_key})")

    market_cap_key = f"{vs_currency}_market_cap"
    change_key = f"{vs_currency}_24h_change"

    return {
        "token_symbol": str(asset["token_symbol"]).upper(),
        "token_name": str(asset["token_name"]),
        "price_usd": float(payload[vs_currency]),
        "market_cap_usd": _optional_float(payload.get(market_cap_key)),
        "price_change_24h_pct": _optional_float(payload.get(change_key)),
        "coingecko_last_updated_at": _unix_to_iso(payload.get("last_updated_at")),
        "queried_at": queried_at,
        "lookup_type": str(asset["lookup_type"]),
        "lookup_value": str(asset.get("coin_id") or asset.get("contract_address") or ""),
    }


def update_history(*, row: dict[str, Any], interval_minutes: int) -> None:
    history_path = PATH_RESOLVER.resolve_path("token_prices_history", str(row["token_symbol"]))
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_payload = _load_history_payload(history_path, token_symbol=str(row["token_symbol"]))

    bucket = _to_interval_bucket(str(row["queried_at"]), interval_minutes)
    history_row = {
        "bucket_start_at": bucket,
        "queried_at": row["queried_at"],
        "coingecko_last_updated_at": row["coingecko_last_updated_at"],
        "price_usd": row["price_usd"],
        "market_cap_usd": row["market_cap_usd"],
        "price_change_24h_pct": row["price_change_24h_pct"],
    }

    replaced = False
    for index, existing in enumerate(history_payload["rows"]):
        if existing["bucket_start_at"] == bucket:
            history_payload["rows"][index] = history_row
            replaced = True
            break

    if not replaced:
        history_payload["rows"].append(history_row)
        history_payload["rows"].sort(key=lambda item: item["bucket_start_at"])

    history_payload["generated_at"] = row["queried_at"]
    history_payload["row_count"] = len(history_payload["rows"])
    write_json(history_payload, history_path)


def _load_history_payload(history_path: Path, *, token_symbol: str) -> dict[str, Any]:
    if history_path.exists():
        with history_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return {
        "dataset_name": "token_price_history",
        "source": "coingecko",
        "token_symbol": token_symbol,
        "generated_at": None,
        "row_count": 0,
        "rows": [],
    }


def _to_interval_bucket(iso_value: str, interval_minutes: int) -> str:
    dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    bucket_minute = (dt.minute // interval_minutes) * interval_minutes
    bucket_dt = dt.replace(minute=bucket_minute, second=0, microsecond=0)
    return bucket_dt.isoformat().replace("+00:00", "Z")


def _unix_to_iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    dt = datetime.fromtimestamp(int(value), tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def main() -> None:
    payload = fetch_price_snapshots()
    print(
        f"已写入价格快照: {LATEST_OUTPUT_PATH} "
        f"(tokens={payload['row_count']}, generated_at={payload['generated_at']})"
    )


if __name__ == "__main__":
    main()
