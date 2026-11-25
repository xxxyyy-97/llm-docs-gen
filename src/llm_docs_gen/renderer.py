"""Генерация .md файла из DocItem."""
from __future__ import annotations

import logging
import shlex
from pathlib import Path

from .config import DocItem, ProjectConfig
from .executor import run

logger = logging.getLogger(__name__)


def _render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Генерирует стандартную Markdown-таблицу."""
    if not headers:
        return ""

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    data_lines = []
    for row in rows:
        safe_row = row[:len(headers)] + [""] * max(0, len(headers) - len(row))
        data_lines.append("| " + " | ".join(safe_row) + " |")

    return "\n".join([header_line, sep_line, *data_lines])


def render_item(item: DocItem, cfg: ProjectConfig) -> str:
    base = Path(cfg.path).expanduser()

    header = (
        f"path: {cfg.path}/{cfg.docs}/{item.file}\n"
        f"descripton:\n{item.description or ''}"
    )

    blocks: list[str] = []

    for c in item.content:
        title = c.title or "Блок"

        # ═══════════════════════════════════════════
        # ВЕТВЛЕНИЕ ПО ТИПУ КОНТЕНТА
        # ═══════════════════════════════════════════

        if c.type == "table":
            logger.debug("Rendering table: %s", title)
            md_table = _render_markdown_table(c.headers or [], c.rows or [])
            blocks.append(f"## {title}\n\n{md_table}")

        elif c.type == "text":
            logger.debug("Rendering text block: %s", title)
            # Просто вставляем тело текста под заголовком
            # Используем strip(), чтобы убрать лишние пробелы в начале/конце YAML-строки
            blocks.append(f"## {title}\n\n{(c.body or '').strip()}")

        elif c.type == "command":
            if not c.cmd:
                logger.warning("Skipping command block without 'cmd' field")
                continue

            # source = " ".join(c.resolved_args)
            prompt = f"➜  projects {shlex.join([c.cmd, *c.resolved_args])}"

            logger.debug("Executing command: %s", prompt)
            try:
                output = run(c.cmd, c.resolved_args, cwd=base)
                logger.debug("Command succeeded (%d chars)", len(output))
            except RuntimeError as e:
                output = f"ОШИБКА ВЫПОЛНЕНИЯ КОМАНДЫ: {e}"
                logger.error("Command failed: %s", e)

            blocks.append(f"## {title}\n\n```bash\n{prompt}\n{output.rstrip()}\n```")

    return "\n\n".join([header, "-"*10, *blocks])


def generate_all(cfg: ProjectConfig) -> list[Path]:
    out_dir = Path(cfg.path).expanduser() / cfg.docs
    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for item in cfg.sorted_items:
        logger.info("Generating file: %s (render=%d)", item.file, item.render)

        content = render_item(item, cfg)
        target = out_dir / item.file
        target.write_text(content, encoding="utf-8")
        created.append(target)

    return created
