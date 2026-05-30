from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.services.llm_client import LLMClient
from backend.app.services.result_writer import write_json

ALLOWED_PROFILE_LABELS = {
    "早期埋伏型",
    "趋势跟随型",
    "深度持有型",
    "高浮盈型",
    "高活跃轮动型",
    "待定观察型",
}

PROMPT_INPUT_FIELDS = [
    "token_symbol",
    "token_name",
    "chain_name",
    "address_key",
    "as_of_date",
    "active_days",
    "first_buy_day",
    "hold_days_est",
    "net_flow_usd",
    "avg_buy_price_usd",
    "token_price_usd",
    "position_value_usd",
    "unrealized_pnl_pct",
]

OUTPUT_FIELDS = ("profile_label", "risk_note", "summary")


@dataclass(slots=True)
class AddressProfileResult:
    address_key: str
    token_symbol: str
    as_of_date: str | None
    profile_label: str
    risk_note: str
    summary: str
    generation_status: str
    error_code: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "address_key": self.address_key,
            "token_symbol": self.token_symbol,
            "as_of_date": self.as_of_date,
            "profile_label": self.profile_label,
            "risk_note": self.risk_note,
            "summary": self.summary,
            "generation_status": self.generation_status,
            "error_code": self.error_code,
        }


class AddressProfileBatchGenerator:
    def __init__(
        self,
        *,
        project_root: str | Path,
        env_path: str | Path | None = None,
        max_retries: int = 1,
        timeout: int = 60,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.max_retries = max_retries
        self.timeout = timeout
        self.llm_client = LLMClient(env_path=env_path)
        self.system_prompt = self._load_system_prompt()

    def build_profiles(
        self,
        *,
        input_path: str | Path,
        output_path: str | Path,
        token_symbol: str = "ETH",
        limit: int | None = None,
    ) -> Path:
        source_payload = self._load_input_payload(input_path, token_symbol=token_symbol)
        source_rows = list(source_payload["rows"])
        if limit is not None:
            source_rows = source_rows[:limit]

        results: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        success_count = 0
        fallback_count = 0

        for row_index, row in enumerate(source_rows):
            result, error = self._build_single_profile(
                row=row,
                row_index=row_index,
                token_symbol=token_symbol,
            )
            results.append(result.to_dict())
            if result.generation_status == "success":
                success_count += 1
            else:
                fallback_count += 1
            if error is not None:
                errors.append(error)

        output_payload = {
            "dataset_name": "token_address_profiles",
            "source_dataset": source_payload["dataset_name"],
            "token_symbol": token_symbol,
            "model_provider": self.llm_client.provider,
            "model_name": self.llm_client.default_model,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_row_count": len(source_payload["rows"]),
            "processed_row_count": len(source_rows),
            "success_count": success_count,
            "fallback_count": fallback_count,
            "error_count": len(errors),
            "rows": results,
            "errors": errors,
        }
        return write_json(output_payload, output_path)

    def _load_system_prompt(self) -> str:
        prompt_path = self.project_root / "prompts" / "address_profile" / "system_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"未找到 system prompt 文件: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8").strip()

    def _load_input_payload(
        self,
        input_path: str | Path,
        *,
        token_symbol: str,
    ) -> dict[str, Any]:
        path = Path(input_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"未找到输入文件: {path}")

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if payload.get("dataset_name") != "address_feature_snapshot":
            raise ValueError(
                "输入数据集不匹配，期望 `address_feature_snapshot`，"
                f"实际为: {payload.get('dataset_name')}"
            )
        if str(payload.get("token_symbol", "")).upper() != token_symbol.upper():
            raise ValueError(
                f"输入 token_symbol 与目标 token 不一致: "
                f"{payload.get('token_symbol')} != {token_symbol}"
            )
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise ValueError("输入文件缺少 `rows` 数组")
        return payload

    def _build_single_profile(
        self,
        *,
        row: dict[str, Any],
        row_index: int,
        token_symbol: str,
    ) -> tuple[AddressProfileResult, dict[str, Any] | None]:
        row_address = str(row.get("address_key", "")).strip() or f"row_{row_index}"
        attempts = self.max_retries + 1
        last_error_code = "UNKNOWN_ERROR"
        last_error_message = "未知错误"

        for _ in range(attempts):
            try:
                self._validate_input_row(row)
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self._build_task_prompt(row)},
                ]
                response = self.llm_client.chat(
                    messages=messages,
                    temperature=0.2,
                    timeout=self.timeout,
                )
                content = self._extract_message_content(response)
                parsed = self._parse_model_output(content)
                profile = self._validate_profile_output(parsed)
                return (
                    AddressProfileResult(
                        address_key=row_address,
                        token_symbol=token_symbol,
                        as_of_date=self._optional_str(row.get("as_of_date")),
                        profile_label=profile["profile_label"],
                        risk_note=profile["risk_note"],
                        summary=profile["summary"],
                        generation_status="success",
                        error_code=None,
                    ),
                    None,
                )
            except Exception as exc:  # noqa: BLE001 - batch job should degrade per row
                last_error_code = self._classify_error(exc)
                last_error_message = str(exc)

        fallback = self._build_fallback_profile(
            row=row,
            token_symbol=token_symbol,
            error_code=last_error_code,
        )
        error_payload = {
            "row_index": row_index,
            "address_key": row_address,
            "error_code": last_error_code,
            "error_message": last_error_message,
        }
        return fallback, error_payload

    def _validate_input_row(self, row: dict[str, Any]) -> None:
        if not isinstance(row, dict):
            raise ValueError("输入 row 必须是对象")
        if not str(row.get("address_key", "")).strip():
            raise ValueError("输入 row 缺少 address_key")
        if not str(row.get("token_symbol", "")).strip():
            raise ValueError("输入 row 缺少 token_symbol")

    def _build_task_prompt(self, row: dict[str, Any]) -> str:
        prompt_payload = {
            field: row.get(field)
            for field in PROMPT_INPUT_FIELDS
            if field in row and row.get(field) is not None
        }
        input_json = json.dumps(prompt_payload, ensure_ascii=False, indent=2)
        return (
            "请基于以下地址结构化特征，生成该地址的行为画像。\n\n"
            "任务要求：\n"
            "1. 只能依据输入字段进行判断，不得补充输入中不存在的背景信息。\n"
            "2. 输出必须克制、可解释、基于证据。\n"
            "3. 不允许输出无证据断言。\n"
            "4. 不允许输出交易建议、价格预测、身份判断或绝对因果结论。\n"
            "5. 若证据不足，请使用 `待定观察型`，并在 `risk_note` 与 `summary` 中说明不确定性。\n"
            "6. 输出必须是单个 JSON 对象，只包含 `profile_label`、`risk_note`、`summary`。\n\n"
            "输入数据：\n"
            f"{input_json}"
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

    def _validate_profile_output(self, payload: dict[str, Any]) -> dict[str, str]:
        normalized = {}
        for field in OUTPUT_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"输出字段无效: {field}")
            normalized[field] = value.strip()

        if normalized["profile_label"] not in ALLOWED_PROFILE_LABELS:
            raise ValueError(f"输出标签超出允许集合: {normalized['profile_label']}")
        if self._contains_disallowed_content(normalized):
            raise ValueError("输出内容超出证据边界")
        return normalized

    def _contains_disallowed_content(self, payload: dict[str, str]) -> bool:
        text = " ".join(payload.values())
        disallowed_patterns = [
            r"建议买入",
            r"建议卖出",
            r"建议加仓",
            r"建议减仓",
            r"建议止盈",
            r"建议止损",
            r"考虑加仓",
            r"考虑减仓",
            r"考虑止盈",
            r"考虑止损",
            r"应当买入",
            r"应当卖出",
            r"应当加仓",
            r"应当减仓",
            r"可以买入",
            r"可以卖出",
            r"可以加仓",
            r"可以减仓",
            r"适合买入",
            r"适合卖出",
            r"买入机会",
            r"卖出机会",
            r"价格将",
            r"必然上涨",
            r"必然下跌",
            r"名人地址",
            r"内幕",
            r"操纵市场",
        ]
        return any(re.search(pattern, text) for pattern in disallowed_patterns)

    def _build_fallback_profile(
        self,
        *,
        row: dict[str, Any],
        token_symbol: str,
        error_code: str,
    ) -> AddressProfileResult:
        address_key = str(row.get("address_key", "")).strip() or "unknown"
        return AddressProfileResult(
            address_key=address_key,
            token_symbol=token_symbol,
            as_of_date=self._optional_str(row.get("as_of_date")),
            profile_label="待定观察型",
            risk_note="当前画像生成未通过校验，已按保守策略降级，需继续观察后续行为一致性。",
            summary=(
                "由于本次模型输出异常、字段缺失或超出证据边界，系统暂将该地址归为待定观察型。"
                "当前结果仅用于稳定落盘，不应视为强结论。"
            ),
            generation_status="fallback",
            error_code=error_code,
        )

    def _classify_error(self, exc: Exception) -> str:
        message = str(exc)
        if "JSON" in message or "json" in message:
            return "INVALID_JSON"
        if "字段" in message:
            return "INVALID_OUTPUT_FIELDS"
        if "标签" in message:
            return "INVALID_PROFILE_LABEL"
        if "证据边界" in message:
            return "OUT_OF_BOUNDS_CONTENT"
        if "address_key" in message or "token_symbol" in message:
            return "INVALID_INPUT_ROW"
        return exc.__class__.__name__.upper()

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
