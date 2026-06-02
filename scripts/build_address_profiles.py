from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.address_profile_generator import AddressProfileBatchGenerator
from backend.app.services.env_loader import load_project_env
from token_batch_utils import (
    DEFAULT_CONFIG_PATH,
    resolve_enabled_token,
    resolve_feature_output_path,
    resolve_processed_input_path,
)

DEFAULT_TOKEN_SYMBOL = "FET"


def resolve_profile_limit(
    *,
    config_path: Path,
    token_symbol: str,
    limit: int | None,
) -> int | None:
    if limit is not None:
        return limit
    token = resolve_enabled_token(config_path, token_symbol)
    return token.address_profile_limit


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线生成地址画像结果")
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="token 配置文件路径",
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=None,
        help="输入特征层 JSON 文件路径",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="输出画像结果 JSON 文件路径",
    )
    parser.add_argument(
        "--token-symbol",
        default=DEFAULT_TOKEN_SYMBOL,
        help="目标 token_symbol，默认 FET",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="调试时仅处理前 N 条记录",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="单条记录的最大重试次数",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="单次 LLM 调用超时时间（秒）",
    )
    parser.add_argument(
        "--all-enabled",
        action="store_true",
        help="按 tokens.json 中所有启用币种批量生成",
    )
    return parser.parse_args(argv)


def run_batch(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    input_path: Path | None = None,
    output_path: Path | None = None,
    token_symbol: str = DEFAULT_TOKEN_SYMBOL,
    limit: int | None = None,
    max_retries: int = 1,
    timeout: int = 60,
) -> Path:
    token_symbol = token_symbol.upper()
    effective_limit = resolve_profile_limit(
        config_path=config_path,
        token_symbol=token_symbol,
        limit=limit,
    )
    env_path = load_project_env(PROJECT_ROOT / ".env")
    generator = AddressProfileBatchGenerator(
        project_root=PROJECT_ROOT,
        env_path=env_path,
        max_retries=max_retries,
        timeout=timeout,
    )
    resolved_input_path = input_path or resolve_processed_input_path(
        "address_feature_snapshot", token_symbol
    )
    resolved_output_path = output_path or resolve_feature_output_path(
        "address_profiles", token_symbol
    )
    return generator.build_profiles(
        input_path=resolved_input_path,
        output_path=resolved_output_path,
        token_symbol=token_symbol,
        limit=effective_limit,
    )


def run_all_enabled(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    limit: int | None = None,
    max_retries: int = 1,
    timeout: int = 60,
) -> list[Path]:
    from token_batch_utils import load_enabled_tokens

    outputs: list[Path] = []
    for token in load_enabled_tokens(config_path):
        token_symbol = token.token_symbol.upper()
        effective_limit = limit if limit is not None else token.address_profile_limit
        if effective_limit is None:
            print(f"开始生成地址画像: {token_symbol}（全量）")
        else:
            print(f"开始生成地址画像: {token_symbol}（最多 {effective_limit} 条）")
        outputs.append(
            run_batch(
                config_path=config_path,
                token_symbol=token_symbol,
                limit=effective_limit,
                max_retries=max_retries,
                timeout=timeout,
            )
        )
    return outputs


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.all_enabled:
        output_paths = run_all_enabled(
            config_path=args.config_path,
            limit=args.limit,
            max_retries=args.max_retries,
            timeout=args.timeout,
        )
        for output_path in output_paths:
            print(f"已生成地址画像结果: {output_path.relative_to(PROJECT_ROOT)}")
        return

    output_path = run_batch(
        config_path=args.config_path,
        input_path=args.input_path,
        output_path=args.output_path,
        token_symbol=args.token_symbol,
        limit=args.limit,
        max_retries=args.max_retries,
        timeout=args.timeout,
    )
    print(f"已生成地址画像结果: {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
