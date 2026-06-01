from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build_address_profiles import run_all_enabled as build_address_profiles_main
from build_feature_layer import main as build_feature_layer_main
from build_token_ai_summary import run_all_enabled as build_token_ai_summary_main
from fetch_token_prices import main as fetch_token_prices_main
from render_sql import main as render_sql_main
from run_dune_queries import main as run_dune_queries_main
from validate_workflow_outputs import main as validate_workflow_outputs_main


STEP_FUNCTIONS: dict[str, tuple[str, Callable[[], None]]] = {
    "render_sql": ("Step 1/7: 渲染 SQL", render_sql_main),
    "run_dune_queries": ("Step 2/7: 拉取 Dune 结果", run_dune_queries_main),
    "build_feature_layer": ("Step 3/7: 生成特征层", build_feature_layer_main),
    "fetch_token_prices": ("Step 4/7: 抓取价格快照", fetch_token_prices_main),
    "build_address_profiles": ("Step 5/7: 生成地址画像", build_address_profiles_main),
    "build_token_ai_summary": ("Step 6/7: 生成 Token AI 总结", build_token_ai_summary_main),
    "validate_outputs": ("Step 7/7: 校验工作流产物", validate_workflow_outputs_main),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="执行链上聪明钱研究工作流")
    parser.add_argument(
        "--skip-steps",
        nargs="*",
        choices=tuple(STEP_FUNCTIONS.keys()),
        default=[],
        help="需要跳过的步骤标识",
    )
    return parser.parse_args(argv)


def run_step(step_name: str, step_func: Callable[[], None]) -> None:
    print(f"\n=== {step_name} ===")
    step_func()
    print(f"=== {step_name} 完成 ===")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    skip_steps = set(args.skip_steps)

    print("开始执行链上聪明钱研究全流程...")
    for step_key, (step_label, step_func) in STEP_FUNCTIONS.items():
        if step_key in skip_steps:
            print(f"\n=== 跳过步骤: {step_label} ===")
            continue
        run_step(step_label, step_func)
    print("\nPipeline 执行完成。")


if __name__ == "__main__":
    main()
