from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.env_loader import load_project_env
from backend.app.services.token_ai_summary_generator import TokenAISummaryGenerator
from token_batch_utils import DEFAULT_CONFIG_PATH, resolve_feature_output_path

DEFAULT_TOKEN_SYMBOL = "FET"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate token-level AI summary JSON")
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="token config path",
    )
    parser.add_argument(
        "--token-symbol",
        default=DEFAULT_TOKEN_SYMBOL,
        help="Token symbol to summarize",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Output summary JSON path",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=7,
        help="Number of latest overview rows to include",
    )
    parser.add_argument(
        "--top-position-limit",
        type=int,
        default=5,
        help="Number of top positions to include in the prompt input",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="LLM request timeout in seconds",
    )
    parser.add_argument(
        "--all-enabled",
        action="store_true",
        help="Generate token summaries for all enabled tokens",
    )
    return parser.parse_args(argv)


def run_batch(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    token_symbol: str = DEFAULT_TOKEN_SYMBOL,
    output_path: Path | None = None,
    lookback_days: int = 7,
    top_position_limit: int = 5,
    timeout: int = 60,
) -> Path:
    token_symbol = token_symbol.upper()
    env_path = load_project_env(PROJECT_ROOT / ".env")
    generator = TokenAISummaryGenerator(
        project_root=PROJECT_ROOT,
        env_path=env_path,
        timeout=timeout,
    )
    resolved_output_path = output_path or resolve_feature_output_path(
        "token_ai_summary", token_symbol
    )
    return generator.build_summary(
        token_symbol=token_symbol,
        output_path=resolved_output_path,
        lookback_days=lookback_days,
        top_position_limit=top_position_limit,
    )


def run_all_enabled(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    lookback_days: int = 7,
    top_position_limit: int = 5,
    timeout: int = 60,
) -> list[Path]:
    from token_batch_utils import load_enabled_tokens

    outputs: list[Path] = []
    for token in load_enabled_tokens(config_path):
        token_symbol = token.token_symbol.upper()
        print(f"开始生成 Token AI 总结: {token_symbol}")
        outputs.append(
            run_batch(
                config_path=config_path,
                token_symbol=token_symbol,
                lookback_days=lookback_days,
                top_position_limit=top_position_limit,
                timeout=timeout,
            )
        )
    return outputs


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.all_enabled:
        output_paths = run_all_enabled(
            config_path=args.config_path,
            lookback_days=args.lookback_days,
            top_position_limit=args.top_position_limit,
            timeout=args.timeout,
        )
        for output_path in output_paths:
            print(f"Generated token AI summary: {output_path.relative_to(PROJECT_ROOT)}")
        return

    output_path = run_batch(
        config_path=args.config_path,
        token_symbol=args.token_symbol,
        output_path=args.output_path,
        lookback_days=args.lookback_days,
        top_position_limit=args.top_position_limit,
        timeout=args.timeout,
    )
    print(f"Generated token AI summary: {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
