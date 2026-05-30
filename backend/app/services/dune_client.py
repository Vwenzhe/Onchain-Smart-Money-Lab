from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any

import requests

from backend.app.services.env_loader import load_project_env


class DuneClient:
    """Dune REST wrapper for parameterized saved queries."""

    def __init__(self, env_path: str | Path | None = None) -> None:
        self.env_path = load_project_env(env_path)
        self.api_key = os.getenv("DUNE_API_KEY", "").strip()
        self.base_url = os.getenv("DUNE_BASE_URL", "https://api.dune.com/api/v1").rstrip("/")
        if not self.api_key:
            raise ValueError(f"未在 {self.env_path} 中设置 DUNE_API_KEY")
        self.headers = {
            "X-Dune-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        response = requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            json=json_body,
            timeout=timeout,
        )
        response.raise_for_status()
        if not response.text.strip():
            return {}
        return response.json()

    def get_latest_result(self, *, query_id: int, limit: int = 1000) -> dict:
        return self._request(
            method="GET",
            path=f"/query/{query_id}/results",
            params={"limit": limit},
        )

    def save_latest_result(
        self,
        *,
        query_id: int,
        raw_output_dir: str | Path,
        output_name: str | None = None,
        limit: int = 1000,
    ) -> Path:
        payload = self.get_latest_result(query_id=query_id, limit=limit)
        output_dir = Path(raw_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / (output_name or f"query_{query_id}_latest.json")
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return file_path

    def update_query_definition(
        self,
        *,
        query_id: int,
        query_name: str,
        sql_text: str,
        parameters: list[dict[str, Any]] | None = None,
    ) -> int:
        payload_body: dict[str, Any] = {
            "query_id": query_id,
            "name": query_name,
            "query_sql": sql_text,
        }
        if parameters is not None:
            payload_body["parameters"] = parameters

        payload = self._request(
            method="PATCH",
            path=f"/query/{query_id}",
            json_body=payload_body,
        )
        return int(payload.get("query_id", query_id))

    def run_parameterized_query(
        self,
        *,
        token_symbol: str,
        sql_name: str,
        query_id: int,
        sql_text: str,
        query_parameters: dict[str, Any],
        parameter_definitions: list[dict[str, Any]],
        raw_output_dir: str | Path,
        performance: str = "medium",
    ) -> Path:
        self.update_query_definition(
            query_id=query_id,
            query_name=f"{sql_name}_parameterized",
            sql_text=sql_text,
            parameters=parameter_definitions,
        )
        execution_id = self.execute_query(
            query_id=query_id,
            query_parameters=query_parameters,
            performance=performance,
        )
        self.wait_for_execution(execution_id=execution_id)
        return self.fetch_results(
            execution_id=execution_id,
            raw_output_dir=raw_output_dir,
            output_name=f"{sql_name}.json",
        )

    def execute_query(
        self,
        *,
        query_id: int,
        query_parameters: dict[str, Any] | None = None,
        performance: str = "medium",
    ) -> str:
        payload = self._request(
            method="POST",
            path=f"/query/{query_id}/execute",
            json_body={
                "query_parameters": query_parameters or {},
                "performance": performance,
            },
        )
        return str(payload["execution_id"])

    def get_execution_status(self, *, execution_id: str) -> dict[str, Any]:
        return self._request(
            method="GET",
            path=f"/execution/{execution_id}/status",
        )

    def wait_for_execution(self, *, execution_id: str, poll_seconds: int = 3) -> dict[str, Any]:
        while True:
            payload = self.get_execution_status(execution_id=execution_id)
            state = payload.get("state")

            if state in {"QUERY_STATE_COMPLETED", "QUERY_STATE_COMPLETED_PARTIAL"}:
                return payload

            if state in {"QUERY_STATE_FAILED", "QUERY_STATE_CANCELED", "QUERY_STATE_EXPIRED"}:
                error = payload.get("error") or {}
                error_message = error.get("message", "未知错误")
                raise RuntimeError(
                    f"Dune 执行失败: execution_id={execution_id}, state={state}, error={error_message}"
                )

            time.sleep(poll_seconds)

    def fetch_results(
        self,
        *,
        execution_id: str,
        raw_output_dir: str | Path,
        output_name: str,
    ) -> Path:
        payload = self._request(
            method="GET",
            path=f"/execution/{execution_id}/results",
            params={"limit": 1000},
        )
        output_dir = Path(raw_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / output_name
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return file_path

    def create_or_update_query(self, *, query_name: str, sql_text: str) -> int:
        raise NotImplementedError(
            "当前版本直接更新既有 query_id；如需自动创建 Query，再补 create_or_update_query()。"
        )
