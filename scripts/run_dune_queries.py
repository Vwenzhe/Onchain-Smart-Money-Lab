from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.config_loader import load_project_config
from backend.app.services.dune_client import DuneClient
from backend.app.services.env_loader import load_project_env
from backend.app.services.sql_renderer import SQLRenderer


def build_query_parameters(token) -> dict[str, str]:
    return {
        "token_symbol": token.token_symbol,
        "token_name": token.token_name,
        "contract_address": token.contract_address.lower(),
        "price_symbol": token.price_symbol,
    }


def build_parameter_definitions(token) -> list[dict[str, str]]:
    query_parameters = build_query_parameters(token)
    return [
        {"key": key, "type": "text", "value": value}
        for key, value in query_parameters.items()
    ]


def main() -> None:
    env_path = load_project_env(PROJECT_ROOT / ".env")

    config = load_project_config(PROJECT_ROOT / "config" / "tokens.json")
    renderer = SQLRenderer(project_root=PROJECT_ROOT)
    renderer.render_all(config)

    dune_client = DuneClient(env_path=env_path)
    template_dir = PROJECT_ROOT / "sql" / "templates" / "eth"

    for token in config.tokens:
        token_symbol = token.token_symbol.upper()
        raw_output_dir = PROJECT_ROOT / "data" / "raw" / "dune" / token_symbol
        dune_query_ids = token.dune_query_ids or {}
        query_parameters = build_query_parameters(token)
        parameter_definitions = build_parameter_definitions(token)

        for sql_file in sorted(template_dir.glob("*.sql")):
            sql_text = sql_file.read_text(encoding="utf-8")
            sql_name = sql_file.stem
            query_id = dune_query_ids.get(sql_name)
            if query_id is None:
                print(
                    f"跳过: {token_symbol}/{sql_file.name}，"
                    "原因: 未在 config/tokens.json 中配置 dune_query_ids"
                )
                continue

            print(
                f"开始执行参数化查询: {token_symbol}/{sql_file.name} "
                f"-> query_id={query_id}, contract_address={token.contract_address}"
            )
            dune_client.run_parameterized_query(
                token_symbol=token_symbol,
                sql_name=sql_name,
                query_id=query_id,
                sql_text=sql_text,
                query_parameters=query_parameters,
                parameter_definitions=parameter_definitions,
                raw_output_dir=raw_output_dir,
            )


if __name__ == "__main__":
    main()
