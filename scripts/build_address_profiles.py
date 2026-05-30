from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.address_profile_generator import AddressProfileBatchGenerator
from backend.app.services.env_loader import load_project_env


DEFAULT_INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "address_feature_snapshot" / "FET.json"
)
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "features" / "address_profiles" / "FET.json"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线生成 FET 地址画像结果")
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="输入特征层 JSON 文件路径",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="输出画像结果 JSON 文件路径",
    )
    parser.add_argument(
        "--token-symbol",
        default="FET",
        help="当前默认传入 FET，便于后续扩展",
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
    return parser.parse_args(argv)


def run_batch(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    token_symbol: str = "FET",
    limit: int | None = None,
    max_retries: int = 1,
    timeout: int = 60,
) -> Path:
    env_path = load_project_env(PROJECT_ROOT / ".env")
    generator = AddressProfileBatchGenerator(
        project_root=PROJECT_ROOT,
        env_path=env_path,
        max_retries=max_retries,
        timeout=timeout,
    )
    return generator.build_profiles(
        input_path=input_path,
        output_path=output_path,
        token_symbol=token_symbol.upper(),
        limit=limit,
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_path = run_batch(
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
