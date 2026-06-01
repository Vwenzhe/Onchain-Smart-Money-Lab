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
RESEARCH_CONCLUSION_FIELDS = (
    "headline",
    "structure_stage",
    "structure_stage_evidence",
    "driver_type",
    "driver_evidence",
    "primary_risk",
    "risk_evidence",
    "drill_down_view",
    "drill_down_focus",
    "drill_down_evidence",
    "evidence_strength",
    "main_uncertainty",
)
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_STRUCTURE_STAGES = {
    "早期吸筹",
    "扩散建仓",
    "盈利扩张",
    "高位分歧",
    "集中兑现",
    "弱修复 / 观望",
}
ALLOWED_DRIVER_TYPES = {"增量流入主导", "存量盈利主导", "混合驱动"}
ALLOWED_PRIMARY_RISKS = {
    "样本时效风险",
    "快照偏差风险",
    "盈利兑现风险",
    "成本带脆弱风险",
    "持续性风险",
}
ALLOWED_DRILL_DOWN_VIEWS = {"值得继续下钻", "暂不值得继续下钻", "可以观察，但不急于继续下钻"}
ALLOWED_EVIDENCE_STRENGTH = {"弱", "中", "强"}


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
            try:
                analysis = self._validate_output(self._parse_model_output(content))
            except Exception:
                repaired = self._repair_output(snapshot=snapshot, raw_content=content)
                analysis = self._validate_output(self._parse_model_output(repaired))
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
        research_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/research_conclusion_prompt.md",
        )
        event_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/event_attribution_prompt.md",
        )
        risk_prompt = load_prompt_text(
            self.project_root,
            "prompts/token_summary/risk_warning_prompt.md",
        )
        return f"{research_prompt}\n\n{event_prompt}\n\n{risk_prompt}"

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
        total_cost = sum(float(row["position_cost_usd_est"]) for row in address_rows)
        total_unrealized_pnl = sum(float(row["unrealized_pnl_usd"]) for row in address_rows)
        profitable_count = sum(
            1 for row in address_rows if float(row["unrealized_pnl_pct"]) > 0
        )
        avg_cost = (
            total_cost / sum(float(row["net_position_token"]) for row in address_rows)
            if address_rows
            else 0.0
        )

        price_latest = self._read_latest_price(token_symbol)
        snapshot_price = float(latest_overview["token_price_usd"])
        latest_price = price_latest["price_usd"] if price_latest is not None else snapshot_price
        price_change_vs_snapshot = (
            (latest_price - snapshot_price) / snapshot_price if snapshot_price else 0.0
        )
        dominant_bucket = self._dominant_bucket(list(pnl_payload["rows"]))
        recent_net_flow_sum = sum(float(row["candidate_net_flow_usd"]) for row in recent_overview[:3])
        trailing_net_flow_sum = sum(float(row["candidate_net_flow_usd"]) for row in recent_overview[3:6])
        recent_address_delta = (
            int(recent_overview[0]["candidate_address_count"]) - int(recent_overview[-1]["candidate_address_count"])
            if len(recent_overview) >= 2
            else 0
        )
        profitable_share = profitable_count / len(address_rows) if address_rows else 0.0
        top_position_concentration = (
            top_position_value / total_position_value if total_position_value else 0.0
        )
        snapshot_gap_days = self._estimate_snapshot_gap_days(
            overview_as_of_date=str(latest_overview["as_of_date"]),
            price_cache_generated_at=price_latest["generated_at"] if price_latest else None,
        )
        preliminary_analysis = self._build_preliminary_analysis(
            profitable_share=profitable_share,
            dominant_bucket=dominant_bucket,
            price_change_vs_snapshot=price_change_vs_snapshot,
            recent_net_flow_sum=recent_net_flow_sum,
            trailing_net_flow_sum=trailing_net_flow_sum,
            recent_address_delta=recent_address_delta,
            latest_price=latest_price,
            avg_cost=avg_cost,
            candidate_address_count=int(latest_overview["candidate_address_count"]),
            snapshot_gap_days=snapshot_gap_days,
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
            "derived_metrics": {
                "top_position_concentration": top_position_concentration,
                "profitable_address_share": profitable_share,
                "dominant_pnl_bucket": dominant_bucket,
                "recent_3row_net_flow_usd": recent_net_flow_sum,
                "previous_3row_net_flow_usd": trailing_net_flow_sum,
                "recent_address_count_delta": recent_address_delta,
                "total_position_value_usd": total_position_value,
                "total_unrealized_pnl_usd": total_unrealized_pnl,
                "avg_buy_price_usd_weighted": avg_cost,
                "price_vs_avg_cost_pct": (
                    (latest_price - avg_cost) / avg_cost if avg_cost else None
                ),
            },
            "preliminary_analysis": preliminary_analysis,
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
            "top_position_concentration": top_position_concentration,
            "total_position_value_usd": total_position_value,
            "snapshot_gap_days": snapshot_gap_days,
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
            "你必须严格遵守以下 JSON 骨架，不得缺字段，不得改字段名：\n"
            f"{self._output_schema_template()}\n\n"
            "输入 JSON：\n"
            f"{input_json}\n"
        )

    def _output_schema_template(self) -> str:
        return json.dumps(
            {
                "trend_summary": "一句到两句中文",
                "market_context": "一句到两句中文",
                "event_attribution": "一句到两句中文",
                "risk_warning": "一句到两句中文",
                "research_conclusion": {
                    "headline": "一句话总结",
                    "structure_stage": "早期吸筹 | 扩散建仓 | 盈利扩张 | 高位分歧 | 集中兑现 | 弱修复 / 观望",
                    "structure_stage_evidence": "结论 + 证据",
                    "driver_type": "增量流入主导 | 存量盈利主导 | 混合驱动",
                    "driver_evidence": "结论 + 证据",
                    "primary_risk": "样本时效风险 | 快照偏差风险 | 盈利兑现风险 | 成本带脆弱风险 | 持续性风险",
                    "risk_evidence": "结论 + 证据",
                    "drill_down_view": "值得继续下钻 | 暂不值得继续下钻 | 可以观察，但不急于继续下钻",
                    "drill_down_focus": "一句话说明最该看哪一层",
                    "drill_down_evidence": "结论 + 证据",
                    "evidence_strength": "弱 | 中 | 强",
                    "main_uncertainty": "一句到两句中文",
                },
                "confidence": "low | medium | high",
            },
            ensure_ascii=False,
            indent=2,
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

    def _validate_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for field in TOKEN_SUMMARY_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"输出字段无效: {field}")
            normalized[field] = value.strip()

        if normalized["confidence"] not in ALLOWED_CONFIDENCE:
            raise ValueError("输出字段无效: confidence")
        research_conclusion_payload = payload.get("research_conclusion")
        if not isinstance(research_conclusion_payload, dict):
            root_level_conclusion = {
                field: payload.get(field)
                for field in RESEARCH_CONCLUSION_FIELDS
                if field in payload
            }
            if root_level_conclusion:
                research_conclusion_payload = root_level_conclusion
        normalized["research_conclusion"] = self._validate_research_conclusion(
            research_conclusion_payload
        )
        if self._contains_disallowed_content(normalized):
            raise ValueError("输出内容超出证据边界")
        return normalized

    def _validate_research_conclusion(self, payload: Any) -> dict[str, str]:
        if not isinstance(payload, dict) or not payload:
            raise ValueError("输出字段无效: research_conclusion")

        normalized: dict[str, str] = {}
        for field in RESEARCH_CONCLUSION_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"输出字段无效: research_conclusion.{field}")
            normalized[field] = value.strip()

        normalized["structure_stage"] = self._normalize_structure_stage(
            normalized["structure_stage"]
        )
        normalized["driver_type"] = self._normalize_driver_type(normalized["driver_type"])
        normalized["primary_risk"] = self._normalize_primary_risk(normalized["primary_risk"])
        normalized["drill_down_view"] = self._normalize_drill_down_view(
            normalized["drill_down_view"]
        )
        normalized["evidence_strength"] = self._normalize_evidence_strength(
            normalized["evidence_strength"]
        )

        if normalized["structure_stage"] not in ALLOWED_STRUCTURE_STAGES:
            raise ValueError("输出字段无效: research_conclusion.structure_stage")
        if normalized["driver_type"] not in ALLOWED_DRIVER_TYPES:
            raise ValueError("输出字段无效: research_conclusion.driver_type")
        if normalized["primary_risk"] not in ALLOWED_PRIMARY_RISKS:
            raise ValueError("输出字段无效: research_conclusion.primary_risk")
        if normalized["drill_down_view"] not in ALLOWED_DRILL_DOWN_VIEWS:
            raise ValueError("输出字段无效: research_conclusion.drill_down_view")
        if normalized["evidence_strength"] not in ALLOWED_EVIDENCE_STRENGTH:
            raise ValueError("输出字段无效: research_conclusion.evidence_strength")
        return normalized

    def _normalize_structure_stage(self, value: str) -> str:
        mapping = {
            "弱修复/观望": "弱修复 / 观望",
            "弱修复 /观望": "弱修复 / 观望",
            "弱修复/ 观望": "弱修复 / 观望",
        }
        return mapping.get(value.strip(), value.strip())

    def _normalize_driver_type(self, value: str) -> str:
        mapping = {
            "增量流入驱动": "增量流入主导",
            "存量盈利驱动": "存量盈利主导",
        }
        return mapping.get(value.strip(), value.strip())

    def _normalize_primary_risk(self, value: str) -> str:
        mapping = {
            "集中度风险": "快照偏差风险",
            "集中风险": "快照偏差风险",
            "地址集中风险": "快照偏差风险",
            "样本偏差风险": "快照偏差风险",
            "时效性风险": "样本时效风险",
        }
        return mapping.get(value.strip(), value.strip())

    def _estimate_snapshot_gap_days(
        self,
        *,
        overview_as_of_date: str,
        price_cache_generated_at: str | None,
    ) -> float:
        if not price_cache_generated_at:
            return 0.0

        snapshot_dt = self._parse_datetime_like(overview_as_of_date)
        price_dt = self._parse_datetime_like(price_cache_generated_at)
        if snapshot_dt is None or price_dt is None:
            return 0.0
        return abs((price_dt - snapshot_dt).total_seconds()) / 86400

    def _parse_datetime_like(self, value: str | None) -> datetime | None:
        if not value:
            return None
        raw = value.strip()
        if not raw:
            return None

        normalized = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d")
            except ValueError:
                return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _normalize_drill_down_view(self, value: str) -> str:
        mapping = {
            "值得下钻": "值得继续下钻",
            "暂不值得下钻": "暂不值得继续下钻",
        }
        return mapping.get(value.strip(), value.strip())

    def _normalize_evidence_strength(self, value: str) -> str:
        mapping = {
            "low": "弱",
            "medium": "中",
            "high": "强",
        }
        return mapping.get(value.strip().lower(), value.strip())

    def _repair_output(self, *, snapshot: dict[str, Any], raw_content: str) -> str:
        repair_prompt = (
            "你上一次输出没有完全符合 JSON 结构要求。"
            "现在你必须只做 JSON 修复，不允许新增无依据事实，不允许输出解释。\n\n"
            "请严格输出下面的 JSON 骨架，保持字段名完全一致：\n"
            f"{self._output_schema_template()}\n\n"
            "你可以参考原始结构化输入：\n"
            f"{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n\n"
            "下面是你上一次的输出，请修复成合法 JSON：\n"
            f"{raw_content}\n"
        )
        response = self.llm_client.chat(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": repair_prompt},
            ],
            temperature=0.0,
            timeout=self.timeout,
        )
        return self._extract_message_content(response)

    def _contains_disallowed_content(self, payload: dict[str, Any]) -> bool:
        text = " ".join(self._flatten_text_values(payload)).lower()
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

    def _flatten_text_values(self, payload: Any) -> list[str]:
        if isinstance(payload, str):
            return [payload]
        if isinstance(payload, dict):
            values: list[str] = []
            for value in payload.values():
                values.extend(self._flatten_text_values(value))
            return values
        if isinstance(payload, list):
            values: list[str] = []
            for item in payload:
                values.extend(self._flatten_text_values(item))
            return values
        return []

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
                f"当前结构主要集中在 `{dominant_bucket}` 这一收益区间，"
                f"浮盈地址占比约 {snapshot['derived_metrics']['profitable_address_share']:.1%}。"
            ),
            "event_attribution": (
                "当前波动更适合被视为结构快照信号。"
                "现有数据不足以支持对催化因素做出强归因。"
            ),
            "risk_warning": (
                f"{timing_gap} 当前更适合关注快照口径带来的样本偏差，以及成本带附近的结构脆弱性。"
            ),
            "research_conclusion": {
                "headline": (
                    f"当前 {snapshot['token_symbol']} 更接近结构信号驱动的观察阶段，"
                    "已有一定活跃度，但证据还不足以支持更强结论。"
                ),
                "structure_stage": str(snapshot["preliminary_analysis"]["structure_stage_hint"]),
                "structure_stage_evidence": (
                    f"当前价格相对快照变动约 {snapshot['price_change_vs_snapshot_pct']:.1%}，"
                    f"主导收益区间为 {dominant_bucket}，更适合先按结构快照理解。"
                ),
                "driver_type": str(snapshot["preliminary_analysis"]["driver_type_hint"]),
                "driver_evidence": (
                    f"最近样本净流入合计约 {snapshot['derived_metrics']['recent_3row_net_flow_usd']:.0f} 美元，"
                    "但仅凭当前快照仍需继续验证驱动持续性。"
                ),
                "primary_risk": str(snapshot["preliminary_analysis"]["primary_risk_hint"]),
                "risk_evidence": (
                    f"当前样本覆盖 {latest['candidate_address_count']} 个候选地址，"
                    f"价格缓存与链上快照相差约 {snapshot.get('snapshot_gap_days', 0.0):.1f} 天。"
                ),
                "drill_down_view": str(snapshot["preliminary_analysis"]["drill_down_view_hint"]),
                "drill_down_focus": str(snapshot["preliminary_analysis"]["drill_down_focus_hint"]),
                "drill_down_evidence": (
                    "当前更适合继续核对头部地址仓位变化与高浮盈样本行为，"
                    "以确认是否存在同步兑现或继续扩散。"
                ),
                "evidence_strength": "弱",
                "main_uncertainty": (
                    "当前输入主要来自链上快照和价格缓存，缺少更长窗口的行为变化与链下催化信息。"
                ),
            },
            "confidence": "low",
        }

    def _build_preliminary_analysis(
        self,
        *,
        profitable_share: float,
        dominant_bucket: str,
        price_change_vs_snapshot: float,
        recent_net_flow_sum: float,
        trailing_net_flow_sum: float,
        recent_address_delta: int,
        latest_price: float,
        avg_cost: float,
        candidate_address_count: int,
        snapshot_gap_days: float,
    ) -> dict[str, str]:
        if profitable_share >= 0.78 and price_change_vs_snapshot > 0.03:
            structure_stage = "盈利扩张"
        elif profitable_share >= 0.72 and recent_net_flow_sum <= trailing_net_flow_sum:
            structure_stage = "高位分歧"
        elif profitable_share < 0.42 and recent_net_flow_sum > 0:
            structure_stage = "扩散建仓"
        elif recent_net_flow_sum < 0 and profitable_share >= 0.7:
            structure_stage = "集中兑现"
        elif abs(price_change_vs_snapshot) <= 0.02:
            structure_stage = "弱修复 / 观望"
        else:
            structure_stage = "扩散建仓"

        if recent_net_flow_sum > 0 and recent_net_flow_sum > trailing_net_flow_sum * 1.1:
            driver_type = "增量流入主导"
        elif profitable_share >= 0.72 and recent_net_flow_sum <= trailing_net_flow_sum:
            driver_type = "存量盈利主导"
        else:
            driver_type = "混合驱动"

        if snapshot_gap_days >= 1.0:
            primary_risk = "样本时效风险"
        elif candidate_address_count <= 20:
            primary_risk = "快照偏差风险"
        elif profitable_share >= 0.78:
            primary_risk = "盈利兑现风险"
        elif avg_cost and latest_price < avg_cost * 1.03:
            primary_risk = "成本带脆弱风险"
        else:
            primary_risk = "持续性风险"

        if structure_stage in {"盈利扩张", "高位分歧", "扩散建仓"}:
            drill_down_view = "值得继续下钻"
        elif structure_stage == "弱修复 / 观望":
            drill_down_view = "可以观察，但不急于继续下钻"
        else:
            drill_down_view = "可以观察，但不急于继续下钻"

        focus = "第三层头部地址仓位明细与画像摘要"
        if primary_risk == "样本时效风险":
            focus = "第二层 freshness 信息与第三层最近快照地址样本"
        elif primary_risk == "快照偏差风险":
            focus = "第二层趋势图与第三层代表性地址样本，验证快照是否失真"
        elif primary_risk == "盈利兑现风险":
            focus = "第三层高浮盈地址的成本、持仓与近期变化"
        elif recent_address_delta > 0:
            focus = "第二层趋势图与第三层新增活跃地址样本"

        return {
            "structure_stage_hint": structure_stage,
            "driver_type_hint": driver_type,
            "primary_risk_hint": primary_risk,
            "drill_down_view_hint": drill_down_view,
            "drill_down_focus_hint": focus,
            "dominant_pnl_bucket_hint": dominant_bucket,
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
