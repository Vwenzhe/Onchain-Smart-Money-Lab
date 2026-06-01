from __future__ import annotations

from pathlib import Path

from backend.app.services.data_registry import DatasetPathResolver
from backend.app.services.config_loader import TokenConfig, load_project_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "tokens.json"
PATH_RESOLVER = DatasetPathResolver(PROJECT_ROOT)


def normalize_token_symbol(token_symbol: str) -> str:
    return token_symbol.strip().upper()


def load_enabled_tokens(config_path: Path = DEFAULT_CONFIG_PATH) -> list[TokenConfig]:
    config = load_project_config(config_path)
    return config.tokens


def resolve_enabled_token(config_path: Path, token_symbol: str) -> TokenConfig:
    token_symbol = normalize_token_symbol(token_symbol)
    for token in load_enabled_tokens(config_path):
        if token.token_symbol.upper() == token_symbol:
            return token
    raise ValueError(f"未在配置中找到已启用 token: {token_symbol}")


def resolve_processed_input_path(dataset_name: str, token_symbol: str) -> Path:
    return PATH_RESOLVER.resolve_path(dataset_name, normalize_token_symbol(token_symbol))


def resolve_feature_output_path(feature_name: str, token_symbol: str) -> Path:
    return PATH_RESOLVER.resolve_path(feature_name, normalize_token_symbol(token_symbol))
