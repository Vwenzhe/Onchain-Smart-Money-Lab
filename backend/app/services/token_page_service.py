from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.repositories.feature_store_repository import (
    DatasetInvalidError,
    DatasetNotFoundError,
    FeatureStoreRepository,
)


FET_DASHBOARD_URL = (
    "https://dune.com/wudide/onchain-smart-money-lab"
    "?utm_source=share&utm_medium=copy&utm_campaign=dashboard"
)


class TokenNotSupportedError(ValueError):
    """Raised when the current API receives a token other than FET."""


class TokenPageService:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.repository = FeatureStoreRepository(self.project_root)

    def get_summary(self, token_symbol: str) -> dict[str, Any]:
        self._ensure_fet(token_symbol)
        overview = self.repository.read_processed_dataset("token_overview_daily", "FET")
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", "FET")

        latest = self._latest_overview_row(overview)
        snapshot_rows = snapshot["rows"]
        total_position_value = sum(float(row["position_value_usd"]) for row in snapshot_rows)
        total_cost = sum(float(row["position_cost_usd_est"]) for row in snapshot_rows)
        total_position = sum(float(row["net_position_token"]) for row in snapshot_rows)
        profitable_count = sum(
            1 for row in snapshot_rows if float(row["unrealized_pnl_pct"]) > 0
        )
        top10_value = sum(
            float(row["position_value_usd"])
            for row in sorted(snapshot_rows, key=lambda item: float(item["position_value_usd"]), reverse=True)[:10]
        )

        profitable_share = profitable_count / len(snapshot_rows) if snapshot_rows else 0.0
        top10_concentration = top10_value / total_position_value if total_position_value else 0.0
        avg_cost = total_cost / total_position if total_position else 0.0

        candidate_count = int(latest["candidate_address_count"])
        net_flow = float(latest["candidate_net_flow_usd"])
        price = float(latest["token_price_usd"])

        return {
            "token_symbol": "FET",
            "token_name": str(latest["token_name"]),
            "chain_name": str(latest["chain_name"]),
            "as_of_date": self._to_iso(str(latest["as_of_date"])),
            "token_price_usd": price,
            "candidate_address_count": candidate_count,
            "candidate_net_position_token": float(latest["candidate_net_position_token"]),
            "candidate_net_flow_usd": net_flow,
            "candidate_avg_net_flow_usd": float(latest["candidate_avg_net_flow_usd"]),
            "avg_buy_price_usd_weighted": avg_cost,
            "profitable_address_share": profitable_share,
            "top10_concentration": top10_concentration,
            "research_summary": (
                f"当前 FET 候选聪明钱地址为 {candidate_count} 个，累计净流入约 "
                f"{net_flow:,.0f} 美元，价格维持在 {price:.4f} 美元附近。"
            ),
            "risk_highlight": self._build_risk_highlight(top10_concentration, profitable_share),
        }

    def get_charts(self, token_symbol: str, days: int = 30) -> dict[str, Any]:
        self._ensure_fet(token_symbol)
        if days < 7 or days > 45:
            raise ValueError("days 必须位于 7 到 45 之间")

        overview = self.repository.read_processed_dataset("token_overview_daily", "FET")
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", "FET")
        pnl_distribution = self.repository.read_processed_dataset("token_pnl_distribution", "FET")

        ordered_rows = list(reversed(overview["rows"]))[-days:]
        total_snapshot_count = max(len(snapshot["rows"]), 1)

        return {
            "labels": [self._to_date_label(str(row["as_of_date"])) for row in ordered_rows],
            "series": {
                "price_usd": [float(row["token_price_usd"]) for row in ordered_rows],
                "candidate_address_count": [int(row["candidate_address_count"]) for row in ordered_rows],
                "candidate_net_flow_usd": [float(row["candidate_net_flow_usd"]) for row in ordered_rows],
                "avg_buy_price_usd": [],
            },
            "pnl_distribution": [
                {
                    "pnl_bucket": str(item["pnl_bucket"]),
                    "pnl_bucket_order": int(item["pnl_bucket_order"]),
                    "address_count": int(item["address_count"]),
                    "address_share": int(item["address_count"]) / total_snapshot_count,
                    "avg_unrealized_pnl_pct": float(item["avg_unrealized_pnl_pct"]),
                    "median_unrealized_pnl_pct": float(item["median_unrealized_pnl_pct"]),
                    "total_position_value_usd": float(item["total_position_value_usd"]),
                    "total_unrealized_pnl_usd": float(item["total_unrealized_pnl_usd"]),
                    "avg_hold_days": float(item["avg_hold_days"]),
                }
                for item in sorted(
                    pnl_distribution["rows"], key=lambda row: int(row["pnl_bucket_order"])
                )
            ],
        }

    def get_top_addresses(
        self,
        token_symbol: str,
        *,
        limit: int = 10,
        sort_by: str = "position_value_usd",
        order: str = "desc",
    ) -> dict[str, Any]:
        self._ensure_fet(token_symbol)
        if sort_by not in {"position_value_usd", "net_flow_usd", "unrealized_pnl_pct"}:
            raise ValueError("sort_by 无效")
        if order not in {"asc", "desc"}:
            raise ValueError("order 无效")

        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", "FET")
        rows = snapshot["rows"]
        max_date = max(self._to_iso(str(row["as_of_date"])) for row in rows)
        min_date = min(self._to_iso(str(row["as_of_date"])) for row in rows)
        reverse = order == "desc"
        sorted_rows = sorted(rows, key=lambda row: float(row[sort_by]), reverse=reverse)[:limit]

        items = []
        stale_count = 0
        for row in rows:
            if self._to_iso(str(row["as_of_date"])) < max_date:
                stale_count += 1

        for row in sorted_rows:
            row_iso = self._to_iso(str(row["as_of_date"]))
            items.append(
                {
                    "address_key": str(row["address_key"]),
                    "as_of_date": row_iso,
                    "active_days": int(row["active_days"]),
                    "first_buy_day": self._optional_iso(row.get("first_buy_day")),
                    "hold_days_est": int(row["hold_days_est"]),
                    "net_position_token": float(row["net_position_token"]),
                    "net_flow_usd": float(row["net_flow_usd"]),
                    "avg_buy_price_usd": float(row["avg_buy_price_usd"]),
                    "token_price_usd": float(row["token_price_usd"]),
                    "position_cost_usd_est": float(row["position_cost_usd_est"]),
                    "position_value_usd": float(row["position_value_usd"]),
                    "unrealized_pnl_usd": float(row["unrealized_pnl_usd"]),
                    "unrealized_pnl_pct": float(row["unrealized_pnl_pct"]),
                    "is_stale_snapshot": row_iso < max_date,
                }
            )

        return {
            "items": items,
            "freshness": {
                "snapshot_min_date": min_date,
                "snapshot_max_date": max_date,
                "stale_row_count": stale_count,
            },
        }

    def get_address_profiles(self, token_symbol: str, limit: int = 6) -> dict[str, Any]:
        self._ensure_fet(token_symbol)
        profiles = self.repository.read_feature_dataset("address_profiles", "FET")
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", "FET")
        snapshot_map = {str(row["address_key"]): row for row in snapshot["rows"]}

        items = []
        label_counter: Counter[str] = Counter()
        for row in profiles["rows"][:limit]:
            label = str(row["profile_label"])
            label_counter[label] += 1
            snapshot_row = snapshot_map.get(str(row["address_key"]), {})
            items.append(
                {
                    "address_key": str(row["address_key"]),
                    "as_of_date": self._optional_iso(row.get("as_of_date")),
                    "profile_label": label,
                    "risk_note": str(row["risk_note"]),
                    "summary": str(row["summary"]),
                    "generation_status": str(row["generation_status"]),
                    "error_code": row.get("error_code"),
                    "active_days": self._optional_int(snapshot_row.get("active_days")),
                    "position_value_usd": self._optional_float(snapshot_row.get("position_value_usd")),
                    "unrealized_pnl_pct": self._optional_float(snapshot_row.get("unrealized_pnl_pct")),
                }
            )

        return {"items": items, "label_summary": dict(label_counter)}

    def get_dune_embeds(self, token_symbol: str) -> dict[str, Any]:
        self._ensure_fet(token_symbol)
        return {
            "items": [
                {
                    "title": "Onchain Smart Money Lab Dashboard",
                    "description": "当前阶段保留 Dune 外链入口，后续可在分享面板中补入具体 embed iframe 链接。",
                    "embed_url": None,
                    "open_url": FET_DASHBOARD_URL,
                    "embed_status": "pending_manual_embed",
                }
            ]
        }

    def get_page(self, token_symbol: str, chart_days: int, top_limit: int, profile_limit: int) -> dict[str, Any]:
        summary = self.get_summary(token_symbol)
        charts = self.get_charts(token_symbol, days=chart_days)
        top_addresses = self.get_top_addresses(token_symbol, limit=top_limit)
        address_profiles = self.get_address_profiles(token_symbol, limit=profile_limit)
        dune_embeds = self.get_dune_embeds(token_symbol)

        return {
            "summary": summary,
            "charts": charts,
            "top_addresses": top_addresses,
            "address_profiles": address_profiles,
            "dune_embeds": dune_embeds,
            "freshness": {
                "overview_latest_date": summary["as_of_date"],
                "snapshot_min_date": top_addresses["freshness"]["snapshot_min_date"],
                "snapshot_max_date": top_addresses["freshness"]["snapshot_max_date"],
                "profile_generated_at": self._profile_generated_at(),
            },
        }

    def _profile_generated_at(self) -> str:
        profiles = self.repository.read_feature_dataset("address_profiles", "FET")
        return self._to_iso(str(profiles["generated_at"]))

    def _latest_overview_row(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload.get("rows")
        if not isinstance(rows, list) or not rows:
            raise DatasetInvalidError("token_overview_daily 缺少 rows")
        return rows[0]

    def _build_risk_highlight(self, top10_concentration: float, profitable_share: float) -> str:
        if top10_concentration >= 0.8:
            return "Top10 地址集中度较高，需关注大额地址行为对结构的影响。"
        if profitable_share >= 0.9:
            return "当前多数样本处于盈利区间，需关注后续是否出现集中兑现。"
        return "当前结构相对分散，但仍需关注样本规模与窗口期带来的偏差。"

    def _ensure_fet(self, token_symbol: str) -> None:
        if token_symbol.upper() != "FET":
            raise TokenNotSupportedError("第一版只支持 FET")

    def _to_iso(self, value: str) -> str:
        normalized = value.replace(" UTC", "+00:00").replace(" ", "T", 1)
        return datetime.fromisoformat(normalized).isoformat().replace("+00:00", "Z")

    def _optional_iso(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return self._to_iso(str(value))

    def _to_date_label(self, value: str) -> str:
        return self._to_iso(value)[:10]

    def _optional_int(self, value: Any) -> int | None:
        if value is None:
            return None
        return int(value)

    def _optional_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)
