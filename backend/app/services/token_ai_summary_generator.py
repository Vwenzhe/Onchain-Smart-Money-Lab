from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.repositories.feature_store_repository import FeatureStoreRepository
from backend.app.services.data_registry import DatasetPathResolver
from backend.app.services.llm_client import LLMClient
from backend.app.services.prompt_loader import load_prompt_text
from backend.app.services.result_writer import write_json

TOKEN_SUMMARY_FIELDS = (
    "trend_summary",
    "market_context",
    "event_attribution",
    "risk_warning",
    "confidence",
)
ALLOWED_CONFIDENCE = {"low", "medium", "high"}


class TokenAISummaryGenerator:
    def __init__(
        self,
        *,
        project_root: str | Path,
        env_path: str | Path | None = None,
        timeout: int = 60,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout
        self.repository = FeatureStoreRepository(self.project_root)
        self.path_resolver = DatasetPathResolver(self.project_root)
        self.llm_client = LLMClient(env_path=env_path)
        self.system_prompt = self._load_system_prompt()
        self.user_prompt_prefix = self._load_user_prompt_prefix()

    def build_summary(
        self,
        *,
        token_symbol: str,
        output_path: str | Path,
        lookback_days: int = 7,
        top_position_limit: int = 5,
    ) -> Path:
        token_symbol = token_symbol.upper()
        snapshot = self._load_snapshot(
            token_symbol=token_symbol,
            lookback_days=lookback_days,
            top_position_limit=top_position_limit,
        )

        generation_status = "success"
        error_code: str | None = None
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self._build_user_prompt(snapshot),
                },
            ]
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.2,
                timeout=self.timeout,
            )
            content = self._extract_message_content(response)
            analysis = self._validate_output(self._parse_model_output(content))
        except Exception as exc:  # noqa: BLE001 - stable file output is preferred
            generation_status = "fallback"
            error_code = self._classify_error(exc)
            analysis = self._build_fallback_analysis(snapshot=snapshot)

        output_payload = {
            "dataset_name": "token_ai_summary",
            "token_symbol": token_symbol,
            "token_name": snapshot["token_name"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_provider": self.llm_client.provider,
            "model_name": self.llm_client.default_model,
            "generation_status": generation_status,
            "error_code": error_code,
            "source_datasets": {
                "token_overview_daily": self.path_resolver.build_reference(
                    "token_overview_daily", token_symbol
                ),
                "token_pnl_distribution": self.path_resolver.build_reference(
                    "token_pnl_distribution", token_symbol
                ),
                "address_feature_snapshot": self.path_resolver.build_reference(
                    "address_feature_snapshot", token_symbol
                ),
                "token_prices_latest": self.path_resolver.build_reference("token_prices_latest"),
            },
            "input_snapshot": snapshot,
            "analysis": analysis,
        }
        return write_json(output_payload, output_path)

    def _load_system_prompt(self) -> str:
        style_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/style_control_prompt.md",
        )
        conservative_rule = load_prompt_text(
            self.project_root,
            "prompts/token_summary/conservative_wording_rule.md",
        )
        return f"{style_prompt}\n\n{conservative_rule}"

    def _load_user_prompt_prefix(self) -> str:
        event_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/event_attribution_prompt.md",
        )
        risk_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/risk_warning_prompt.md",
        )
        return f"{event_prompt}\n\n{risk_prompt}"

    def _load_snapshot(
        self,
        *,
        token_symbol: str,
        lookback_days: int,
        top_position_limit: int,
    ) -> dict[str, Any]:
        overview_payload = self.repository.read_processed_dataset("token_overview_daily", token_symbol)
        pnl_payload = self.repository.read_processed_dataset("token_pnl_distribution", token_symbol)
        address_payload = self.repository.read_processed_dataset("address_feature_snapshot", token_symbol)

        overview_rows = list(overview_payload["rows"])
        latest_overview = overview_rows[0]
        recent_overview = overview_rows[:lookback_days]
        address_rows = list(address_payload["rows"])
        top_positions = sorted(
            address_rows,
            key=lambda row: float(row["position_value_usd"]),
            reverse=True,
        )[:top_position_limit]
        total_position_value = sum(float(row["position_value_usd"]) for row in address_rows)
        top_position_value = sum(float(row["position_value_usd"]) for row in top_positions)

        price_latest = self._read_latest_price(token_symbol)
        snapshot_price = float(latest_overview["token_price_usd"])
        latest_price = price_latest["price_usd"] if price_latest is not None else snapshot_price
        price_change_vs_snapshot = (
            (latest_price - snapshot_price) / snapshot_price if snapshot_price else 0.0
        )

        return {
            "token_symbol": token_symbol,
            "token_name": str(latest_overview["token_name"]),
            "chain_name": str(latest_overview["chain_name"]),
            "overview_as_of_date": str(latest_overview["as_of_date"]),
            "price_cache_generated_at": price_latest["generated_at"] if price_latest else None,
            "price_cache_last_updated_at": (
                price_latest["coingecko_last_updated_at"] if price_latest else None
            ),
            "latest_price_usd": latest_price,
            "snapshot_price_usd": snapshot_price,
            "price_change_vs_snapshot_pct": price_change_vs_snapshot,
            "latest_overview": {
                "candidate_address_count": int(latest_overview["candidate_address_count"]),
                "eligible_address_count": int(latest_overview["eligible_address_count"]),
                "candidate_net_flow_usd": float(latest_overview["candidate_net_flow_usd"]),
                "candidate_avg_net_flow_usd": float(latest_overview["candidate_avg_net_flow_usd"]),
                "candidate_net_position_token": float(latest_overview["candidate_net_position_token"]),
                "token_price_usd": snapshot_price,
            },
            "recent_overview": [
                {
                    "as_of_date": str(row["as_of_date"]),
                    "candidate_address_count": int(row["candidate_address_count"]),
                    "candidate_net_flow_usd": float(row["candidate_net_flow_usd"]),
                    "candidate_net_position_token": float(row["candidate_net_position_token"]),
                    "token_price_usd": float(row["token_price_usd"]),
                }
                for row in recent_overview
            ],
            "pnl_distribution": [
                {
                    "pnl_bucket": str(row["pnl_bucket"]),
                    "address_count": int(row["address_count"]),
                    "avg_unrealized_pnl_pct": float(row["avg_unrealized_pnl_pct"]),
                    "median_unrealized_pnl_pct": float(row["median_unrealized_pnl_pct"]),
                    "total_position_value_usd": float(row["total_position_value_usd"]),
                    "total_unrealized_pnl_usd": float(row["total_unrealized_pnl_usd"]),
                    "avg_hold_days": float(row["avg_hold_days"]),
                }
                for row in sorted(
                    pnl_payload["rows"],
                    key=lambda item: int(item["pnl_bucket_order"]),
                )
            ],
            "top_positions": [
                {
                    "address_key": str(row["address_key"]),
                    "as_of_date": str(row["as_of_date"]),
                    "active_days": int(row["active_days"]),
                    "hold_days_est": int(row["hold_days_est"]),
                    "net_flow_usd": float(row["net_flow_usd"]),
                    "position_value_usd": float(row["position_value_usd"]),
                    "unrealized_pnl_pct": float(row["unrealized_pnl_pct"]),
                }
                for row in top_positions
            ],
            "top_position_concentration": (
                top_position_value / total_position_value if total_position_value else 0.0
            ),
            "total_position_value_usd": total_position_value,
        }

    def _read_latest_price(self, token_symbol: str) -> dict[str, Any] | None:
        try:
            payload = self.repository.read_global_feature_dataset("token_prices_latest")
        except FileNotFoundError:
            return None

        rows = payload.get("rows")
        if not isinstance(rows, list):
            return None

        matched = next(
            (
                row
                for row in rows
                if str(row.get("token_symbol", "")).upper() == token_symbol
            ),
            None,
        )
        if matched is None:
            return None

        return {
            "generated_at": payload.get("generated_at"),
            "coingecko_last_updated_at": matched.get("coingecko_last_updated_at"),
            "price_usd": float(matched["price_usd"]),
        }

    def _build_user_prompt(self, snapshot: dict[str, Any]) -> str:
        input_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        return (
            f"{self.user_prompt_prefix}\n\n"
            "现在请基于下面的结构化数据生成 token 级市场总结。\n"
            "只能使用提供的数据，分析必须克制、可解释，并且只输出 JSON。\n"
            "除 `confidence` 之外，其余字段内容必须全部使用简体中文。\n\n"
            "输入 JSON：\n"
            f"{input_json}\n"
        )

    def _extract_message_content(self, response: dict[str, Any]) -> str:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("模型返回缺少 choices")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = str(item.get("text", "")).strip()
                    if text:
                        text_parts.append(text)
            if text_parts:
                return "\n".join(text_parts)

        raise ValueError("模型返回缺少 message.content")

    def _parse_model_output(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            candidate = cleaned[start : end + 1]
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed

        raise ValueError("模型输出不是合法 JSON 对象")

    def _validate_output(self, payload: dict[str, Any]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for field in TOKEN_SUMMARY_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"输出字段无效: {field}")
            normalized[field] = value.strip()

        if normalized["confidence"] not in ALLOWED_CONFIDENCE:
            raise ValueError("输出字段无效: confidence")
        if self._contains_disallowed_content(normalized):
            raise ValueError("输出内容超出证据边界")
        return normalized

    def _contains_disallowed_content(self, payload: dict[str, str]) -> bool:
        text = " ".join(payload.values()).lower()
        disallowed_patterns = [
            r"建议买入",
            r"建议卖出",
            r"建议加仓",
            r"建议减仓",
            r"buy now",
            r"sell now",
            r"strong buy",
            r"strong sell",
            r"will surge",
            r"will dump",
            r"必然上涨",
            r"必然下跌",
            r"内幕",
            r"操纵市场",
            r"market manipulation",
            r"inside(r|) trading",
        ]
        return any(re.search(pattern, text) for pattern in disallowed_patterns)

    def _build_fallback_analysis(self, *, snapshot: dict[str, Any]) -> dict[str, str]:
        latest = snapshot["latest_overview"]
        dominant_bucket = self._dominant_bucket(snapshot["pnl_distribution"])
        timing_gap = "价格缓存时间与链上快照时间存在差异。" if (
            snapshot.get("price_cache_generated_at")
            and snapshot.get("price_cache_generated_at") != snapshot.get("overview_as_of_date")
        ) else "价格缓存时间与链上快照时间相对接近。"

        return {
            "trend_summary": (
                f"当前缓存价格为 {snapshot['latest_price_usd']:.6f} 美元，最新链上概览覆盖 "
                f"{latest['candidate_address_count']} 个候选地址，对应净流入约 "
                f"{latest['candidate_net_flow_usd']:.0f} 美元。"
            ),
            "market_context": (
                f"当前结构主要集中在 `{dominant_bucket}` 这一收益区间，头部跟踪仓位约占 "
                f"{snapshot['top_position_concentration']:.1%} 的总跟踪仓位价值。"
            ),
            "event_attribution": (
                "当前波动更适合被视为结构快照信号。"
                "现有数据不足以支持对催化因素做出强归因。"
            ),
            "risk_warning": (
                f"{timing_gap} 头部集中度和浮盈分布仍需持续监控，以防出现同步兑现风险。"
            ),
            "confidence": "low",
        }

    def _dominant_bucket(self, pnl_distribution: list[dict[str, Any]]) -> str:
        if not pnl_distribution:
            return "unknown"
        dominant = max(
            pnl_distribution,
            key=lambda row: float(row["total_position_value_usd"]),
        )
        return str(dominant["pnl_bucket"])

    def _classify_error(self, exc: Exception) -> str:
        message = str(exc)
        if "JSON" in message or "json" in message:
            return "INVALID_JSON"
        if "字段" in message or "field" in message.lower():
            return "INVALID_OUTPUT_FIELDS"
        if "证据边界" in message:
            return "OUT_OF_BOUNDS_CONTENT"
        return exc.__class__.__name__.upper()
