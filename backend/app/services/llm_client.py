from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from backend.app.services.env_loader import load_project_env


class LLMClient:
    """DeepSeek chat client wrapper.

    使用 DeepSeek 标准 `chat/completions` 接口，便于后续地址画像能力接入。
    """

    def __init__(self, env_path: str | Path | None = None) -> None:
        self.env_path = load_project_env(env_path)

        provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
        self.provider = provider

        if provider != "deepseek":
            raise ValueError(
                f"当前仅支持 LLM_PROVIDER=deepseek，实际收到: {provider}"
            )

        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        ).rstrip("/")
        self.default_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

        if not self.api_key:
            raise ValueError(f"未在 {self.env_path} 中设置 DEEPSEEK_API_KEY")

    def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Call DeepSeek `chat/completions` API with OpenAI-style messages."""

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
