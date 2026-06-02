from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_TOKEN_FIELDS = [
    "token_symbol",
    "token_name",
    "chain_name",
    "contract_address",
    "price_contract_address",
    "lookback_days",
    "min_active_days",
    "min_net_flow_usd",
]


@dataclass(slots=True)
class TokenConfig:
    token_symbol: str
    token_name: str
    chain_name: str
    contract_address: str
    price_contract_address: str
    lookback_days: int
    min_active_days: int
    min_net_flow_usd: float
    is_enabled: bool = True
    dune_query_ids: dict[str, int] | None = None
    address_profile_limit: int | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TokenConfig":
        missing = [field for field in REQUIRED_TOKEN_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"token 配置缺少必填字段: {', '.join(missing)}")
        return cls(
            token_symbol=str(payload["token_symbol"]),
            token_name=str(payload["token_name"]),
            chain_name=str(payload["chain_name"]),
            contract_address=str(payload["contract_address"]).lower(),
            price_contract_address=str(payload["price_contract_address"]).lower(),
            lookback_days=int(payload["lookback_days"]),
            min_active_days=int(payload["min_active_days"]),
            min_net_flow_usd=float(payload["min_net_flow_usd"]),
            is_enabled=bool(payload.get("is_enabled", True)),
            dune_query_ids={
                str(key): int(value)
                for key, value in dict(payload.get("dune_query_ids", {})).items()
            }
            or None,
            address_profile_limit=(
                int(payload["address_profile_limit"])
                if payload.get("address_profile_limit") is not None
                else None
            ),
        )


@dataclass(slots=True)
class ProjectConfig:
    version: str
    defaults: dict[str, Any]
    tokens: list[TokenConfig]


def load_project_config(config_path: str | Path) -> ProjectConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到配置文件: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    tokens = [TokenConfig.from_dict(item) for item in payload.get("tokens", [])]
    enabled_tokens = [token for token in tokens if token.is_enabled]
    if not enabled_tokens:
        raise ValueError("tokens.json 中没有启用状态的 token")

    return ProjectConfig(
        version=str(payload.get("version", "phase1-v1")),
        defaults=dict(payload.get("defaults", {})),
        tokens=enabled_tokens,
    )
