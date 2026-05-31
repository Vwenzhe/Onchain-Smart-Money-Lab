from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from backend.app.services.env_loader import get_required_env


class CoinGeckoApiError(RuntimeError):
    """Raised when CoinGecko API returns an error."""


@dataclass(slots=True)
class CoinGeckoEndpointConfig:
    base_url: str
    header_name: str


class CoinGeckoClient:
    def __init__(self, env_path: str | None = None, timeout_seconds: int = 30) -> None:
        self.api_key = get_required_env("COINGECKO_API_KEY", env_path)
        self.plan = self._resolve_plan(env_path)
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_prices_by_ids(
        self,
        coin_ids: list[str],
        *,
        vs_currency: str = "usd",
        include_market_cap: bool = True,
        include_24hr_change: bool = True,
        include_last_updated_at: bool = True,
    ) -> dict[str, Any]:
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": vs_currency,
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_change": str(include_24hr_change).lower(),
            "include_last_updated_at": str(include_last_updated_at).lower(),
        }
        return self._request("/simple/price", params=params)

    def get_prices_by_contracts(
        self,
        asset_platform_id: str,
        contract_addresses: list[str],
        *,
        vs_currency: str = "usd",
        include_market_cap: bool = True,
        include_24hr_change: bool = True,
        include_last_updated_at: bool = True,
    ) -> dict[str, Any]:
        path = f"/simple/token_price/{asset_platform_id}"
        params = {
            "contract_addresses": ",".join(address.lower() for address in contract_addresses),
            "vs_currencies": vs_currency,
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_change": str(include_24hr_change).lower(),
            "include_last_updated_at": str(include_last_updated_at).lower(),
        }
        return self._request(path, params=params)

    def _resolve_plan(self, env_path: str | None) -> str:
        try:
            plan = get_required_env("COINGECKO_API_PLAN", env_path).lower()
        except ValueError:
            plan = "auto"
        if plan not in {"auto", "demo", "pro"}:
            raise ValueError("COINGECKO_API_PLAN 仅支持 auto/demo/pro")
        return plan

    def _request(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for endpoint in self._candidate_endpoints():
            try:
                response = self.session.get(
                    f"{endpoint.base_url}{path}",
                    params=params,
                    headers={
                        endpoint.header_name: self.api_key,
                        "Accept": "application/json",
                    },
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 200:
                    return response.json()
                last_error = CoinGeckoApiError(
                    f"CoinGecko 请求失败: {response.status_code} {response.text[:200]}"
                )
            except requests.RequestException as exc:
                last_error = CoinGeckoApiError(f"CoinGecko 请求异常: {exc}")

        if last_error is None:
            raise CoinGeckoApiError("CoinGecko 请求失败，且未获得可用响应")
        raise last_error

    def _candidate_endpoints(self) -> list[CoinGeckoEndpointConfig]:
        if self.plan == "pro":
            return [self._pro_endpoint()]
        if self.plan == "demo":
            return [self._demo_endpoint()]
        return [self._pro_endpoint(), self._demo_endpoint()]

    def _pro_endpoint(self) -> CoinGeckoEndpointConfig:
        return CoinGeckoEndpointConfig(
            base_url="https://pro-api.coingecko.com/api/v3",
            header_name="x-cg-pro-api-key",
        )

    def _demo_endpoint(self) -> CoinGeckoEndpointConfig:
        return CoinGeckoEndpointConfig(
            base_url="https://api.coingecko.com/api/v3",
            header_name="x-cg-demo-api-key",
        )
