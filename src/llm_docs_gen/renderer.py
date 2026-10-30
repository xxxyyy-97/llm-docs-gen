"""Генерация .md файла из DocItem."""
from __future__ import annotations
import logging
import shlex
from pathlib import Path

from .config import DocItem, ProjectConfig
from .executor import run

logger = logging.getLogger(__name__)


def render_item(item: DocItem, cfg: ProjectConfig, *, verbose: bool = False) -> str:
    base = Path(cfg.path).expanduser()

    header = (
        f"path: {cfg.path}/{cfg.docs}/{item.file}\n"
        f"descripton:\n{item.description or ''}"
    )
    blocks: list[str] = []
    for c in item.content:
        source = " ".join(c.resolved_args)
        title = c.title or source
        prompt = f"{shlex.join([c.cmd, *c.resolved_args])}"

        if verbose:
            logger.debug("Executing command: %s", prompt)

        try:
            output = run(c.cmd, c.resolved_args, cwd=base)
            if verbose:
                logger.debug("Command succeeded (%d chars)", len(output))
        except RuntimeError as e:
            output = f"ОШИБКА ВЫПОЛНЕНИЯ КОМАНДЫ: {e}"
            logger.error("Command failed: %s", e)

        # вывод обёрнут в кодовый блок
        blocks.append(f"## {title}\n\n```bash\n{prompt}\n{output.rstrip()}\n```")

    # пустая строка между блоками — важно для Markdown
    return "\n\n".join([header, "-"*10, *blocks])


def generate_all(cfg: ProjectConfig, *, verbose: bool = False) -> list[Path]:
    out_dir = Path(cfg.path).expanduser() / cfg.docs   # ← ОБЯЗАТЕЛЬНО expanduser
    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for item in cfg.sorted_items:
        if verbose:
            logger.info("Generating file: %s (render=%d)", item.file, item.render)
        content = render_item(item, cfg)
        target = out_dir / item.file
        target.write_text(content, encoding="utf-8")
        created.append(target)

    return created
