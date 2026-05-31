from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.app.services.config_loader import TokenConfig, load_project_config
from backend.app.repositories.feature_store_repository import (
    DatasetInvalidError,
    DatasetNotFoundError,
    FeatureStoreRepository,
)


DEFAULT_DASHBOARD_URL = (
    "https://dune.com/wudide/onchain-smart-money-lab"
    "?utm_source=share&utm_medium=copy&utm_campaign=dashboard"
)
BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


class TokenNotSupportedError(ValueError):
    """Raised when the current API receives a token other than FET."""


class TokenPageService:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self.repository = FeatureStoreRepository(self.project_root)
        config = load_project_config(self.project_root / "config" / "tokens.json")
        self.token_configs = {
            token.token_symbol.upper(): token
            for token in config.tokens
        }

    def get_token_meta(self, token_symbol: str) -> dict[str, str]:
        token = self._resolve_token(token_symbol)
        return {
            "token_symbol": token.token_symbol.upper(),
            "chain_name": token.chain_name,
        }

    def get_summary(self, token_symbol: str) -> dict[str, Any]:
        token = self._resolve_token(token_symbol)
        token_symbol = token.token_symbol.upper()
        overview = self.repository.read_processed_dataset("token_overview_daily", token_symbol)
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", token_symbol)
        ai_summary = self._get_ai_summary(token_symbol)

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
            "token_symbol": token_symbol,
            "token_name": str(latest.get("token_name", token.token_name)),
            "chain_name": str(latest.get("chain_name", token.chain_name)),
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
                ai_summary["trend_summary"]
                if ai_summary is not None
                else (
                    f"当前 {token_symbol} 候选聪明钱地址为 {candidate_count} 个，累计净流入约 "
                    f"{net_flow:,.0f} 美元，价格维持在 {price:.4f} 美元附近。"
                )
            ),
            "risk_highlight": (
                ai_summary["risk_warning"]
                if ai_summary is not None
                else self._build_risk_highlight(top10_concentration, profitable_share)
            ),
            "ai_summary": ai_summary,
        }

    def get_charts(self, token_symbol: str, days: int = 30) -> dict[str, Any]:
        token = self._resolve_token(token_symbol)
        token_symbol = token.token_symbol.upper()
        if days < 7 or days > 45:
            raise ValueError("days 必须位于 7 到 45 之间")

        overview = self.repository.read_processed_dataset("token_overview_daily", token_symbol)
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", token_symbol)
        pnl_distribution = self.repository.read_processed_dataset("token_pnl_distribution", token_symbol)

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
        token = self._resolve_token(token_symbol)
        token_symbol = token.token_symbol.upper()
        if sort_by not in {"position_value_usd", "net_flow_usd", "unrealized_pnl_pct"}:
            raise ValueError("sort_by 无效")
        if order not in {"asc", "desc"}:
            raise ValueError("order 无效")

        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", token_symbol)
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
        token = self._resolve_token(token_symbol)
        token_symbol = token.token_symbol.upper()
        profiles = self.repository.read_feature_dataset("address_profiles", token_symbol)
        snapshot = self.repository.read_processed_dataset("address_feature_snapshot", token_symbol)
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
        token = self._resolve_token(token_symbol)
        token_symbol = token.token_symbol.upper()
        return {
            "items": [
                {
                    "title": f"{token_symbol} Onchain Smart Money Dashboard",
                    "description": (
                        f"当前阶段为 {token_symbol} 保留统一 Dune 外链入口，后续可继续补充"
                        " 更细的单币研究视图。"
                    ),
                    "embed_url": None,
                    "open_url": DEFAULT_DASHBOARD_URL,
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
        ai_summary = summary.get("ai_summary")

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
                "profile_generated_at": self._profile_generated_at(token_symbol),
                "ai_summary_generated_at": (
                    ai_summary["generated_at"] if isinstance(ai_summary, dict) else None
                ),
                "price_cache_generated_at": (
                    ai_summary["price_cache_generated_at"] if isinstance(ai_summary, dict) else None
                ),
                "price_cache_last_updated_at": (
                    ai_summary["price_cache_last_updated_at"] if isinstance(ai_summary, dict) else None
                ),
            },
        }

    def _profile_generated_at(self, token_symbol: str) -> str:
        profiles = self.repository.read_feature_dataset("address_profiles", token_symbol.upper())
        return self._to_iso(str(profiles["generated_at"]))

    def _get_ai_summary(self, token_symbol: str) -> dict[str, Any] | None:
        try:
            payload = self.repository.read_feature_dataset("token_ai_summary", token_symbol)
        except DatasetNotFoundError:
            return None

        analysis = payload.get("analysis")
        if not isinstance(analysis, dict):
            raise DatasetInvalidError("token_ai_summary 缺少 analysis")
        input_snapshot = payload.get("input_snapshot")
        if not isinstance(input_snapshot, dict):
            raise DatasetInvalidError("token_ai_summary 缺少 input_snapshot")

        return {
            "generated_at": self._to_iso(str(payload["generated_at"])),
            "generation_status": str(payload.get("generation_status", "unknown")),
            "error_code": payload.get("error_code"),
            "price_cache_generated_at": self._optional_iso(
                input_snapshot.get("price_cache_generated_at")
            ),
            "price_cache_last_updated_at": self._optional_iso(
                input_snapshot.get("price_cache_last_updated_at")
            ),
            "trend_summary": str(analysis.get("trend_summary", "")),
            "market_context": str(analysis.get("market_context", "")),
            "event_attribution": str(analysis.get("event_attribution", "")),
            "risk_warning": str(analysis.get("risk_warning", "")),
            "confidence": str(analysis.get("confidence", "")),
        }

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

    def _resolve_token(self, token_symbol: str) -> TokenConfig:
        normalized = token_symbol.strip().upper()
        token = self.token_configs.get(normalized)
        if token is None:
            raise TokenNotSupportedError(f"当前不支持 token: {token_symbol}")
        return token

    def _to_iso(self, value: str) -> str:
        normalized = value.strip().replace(" UTC", "+00:00").replace("Z", "+00:00")
        if "T" not in normalized and " " in normalized:
            normalized = normalized.replace(" ", "T", 1)

        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(BEIJING_TZ).isoformat(timespec="seconds")

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
