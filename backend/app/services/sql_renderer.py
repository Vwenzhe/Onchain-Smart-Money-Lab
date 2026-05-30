from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from backend.app.services.config_loader import ProjectConfig, TokenConfig


class SQLRenderer:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.template_root = self.project_root / "sql" / "templates"
        self.shared_template_root = self.template_root / "shared"
        self.source_sql_root = self.template_root / "eth"
        self.render_root = self.project_root / "sql" / "rendered"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_root)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_all(self, config: ProjectConfig) -> list[Path]:
        rendered_files: list[Path] = []
        for token in config.tokens:
            rendered_files.extend(self.render_token(token))
        return rendered_files

    def render_token(self, token: TokenConfig) -> list[Path]:
        token_dir = self.render_root / token.token_symbol.upper()
        token_dir.mkdir(parents=True, exist_ok=True)

        token_config_cte = self._render_token_config_cte(token)
        rendered_files: list[Path] = []

        for sql_file in sorted(self.source_sql_root.glob("*.sql")):
            sql_text = sql_file.read_text(encoding="utf-8")
            rendered_sql = self._replace_token_config_cte(sql_text, token_config_cte)
            target_path = token_dir / sql_file.name
            target_path.write_text(rendered_sql, encoding="utf-8")
            rendered_files.append(target_path)

        return rendered_files

    def _render_token_config_cte(self, token: TokenConfig) -> str:
        template = self.env.get_template("shared/token_config.sql.j2")
        return template.render(token=asdict(token)).strip()

    @staticmethod
    def _replace_token_config_cte(sql_text: str, token_config_cte: str) -> str:
        marker = "with token_config as"
        lowered = sql_text.lower()
        start = lowered.find(marker)
        if start == -1:
            raise ValueError("模板 SQL 顶部缺少 token_config CTE，无法渲染")

        open_paren = lowered.find("(", start)
        if open_paren == -1:
            raise ValueError("token_config CTE 结构不完整")

        depth = 0
        close_paren = -1
        for index in range(open_paren, len(sql_text)):
            char = sql_text[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    close_paren = index
                    break

        if close_paren == -1:
            raise ValueError("未找到 token_config CTE 的结束位置")

        cursor = close_paren + 1
        while cursor < len(sql_text) and sql_text[cursor].isspace():
            cursor += 1
        if cursor >= len(sql_text) or sql_text[cursor] != ",":
            raise ValueError("token_config CTE 后缺少逗号，无法安全替换")

        rest_sql = sql_text[cursor + 1 :].lstrip()
        return f"with {token_config_cte},\n{rest_sql}"
