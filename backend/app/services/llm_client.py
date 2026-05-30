from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from backend.app.services.env_loader import load_project_env


class LLMClient:
    """OpenAI-compatible client wrapper.

    默认读取 DeepSeek 配置，也兼容 OpenAI 风格接口，便于后续地址画像能力接入。
    """

    def __init__(self, env_path: str | Path | None = None) -> None:
        self.env_path = load_project_env(env_path)

        provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
        self.provider = provider

        if provider == "deepseek":
            self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
            self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
            self.default_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            raise ValueError(f"暂不支持的 LLM_PROVIDER: {provider}")

        if not self.api_key:
            raise ValueError(f"未在 {self.env_path} 中设置 {self.provider} 的 API Key")

    def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> dict[str, Any]:
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
