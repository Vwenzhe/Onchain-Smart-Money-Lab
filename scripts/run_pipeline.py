from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build_address_profiles import run_batch as build_address_profiles_main
from build_feature_layer import main as build_feature_layer_main
from render_sql import main as render_sql_main
from run_dune_queries import main as run_dune_queries_main


def run_step(step_name: str, step_func) -> None:
    print(f"\n=== {step_name} ===")
    step_func()
    print(f"=== {step_name} 完成 ===")


def main() -> None:
    print("开始执行链上聪明钱研究全流程...")
    run_step("Step 1/4: 渲染 SQL", render_sql_main)
    run_step("Step 2/4: 拉取 Dune 结果", run_dune_queries_main)
    run_step("Step 3/4: 生成特征层", build_feature_layer_main)
    run_step("Step 4/4: 生成地址画像", build_address_profiles_main)
    print("\nPipeline 执行完成。")


if __name__ == "__main__":
    main()
