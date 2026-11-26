import logging
import shlex
from pathlib import Path
from ..models import DocItem, ProjectConfig # , ContentItem
from ..execution import run
from .language import detect_lang
from .blocks import render_markdown_table, render_alert #, render_command_block

logger = logging.getLogger(__name__)
def render_item(item: DocItem, cfg: ProjectConfig) -> str:
    base = Path(cfg.path).expanduser()

    header = (
        f"path: {cfg.path}/{cfg.docs}/{item.file}\n"
        f"descripton:\n{item.description or ''}"
    )

    blocks: list[str] = []

    for c in item.content:
        heading_prefix = "#" * c.title_level

        if c.type == "table":
            title_text = c.title or "Блок"
            logger.debug("Rendering table: %s (level=%d)", title_text, c.title_level)
            md_table = render_markdown_table(c.headers or [], c.rows or [])
            blocks.append(f"{heading_prefix} {title_text}\n\n{md_table}")

        elif c.type == "text":
            title_text = c.title or "Блок"
            logger.debug("Rendering text block: %s (level=%d)", title_text, c.title_level)
            blocks.append(f"{heading_prefix} {title_text}\n\n{(c.body or '').strip()}")

        elif c.type == "alert":
            logger.debug("Rendering alert [%s]", c.alert)
            alert_md = render_alert(c.alert, c.body or "")
            if c.title:
                blocks.append(f"{heading_prefix} {c.title}\n\n{alert_md}")
            else:
                blocks.append(alert_md)

        elif c.type == "command":
            if not c.cmd:
                logger.warning("Skipping command block without 'cmd' field")
                continue

            title_text = c.title or " ".join(c.resolved_args)
            prompt = shlex.join([c.cmd, *c.resolved_args])

            logger.debug("Executing command: %s (level=%d)", prompt, c.title_level)
            try:
                output = run(c.cmd, c.resolved_args, cwd=base)
                logger.debug("Command succeeded (%d chars)", len(output))
            except RuntimeError as e:
                output = f"ОШИБКА ВЫПОЛНЕНИЯ КОМАНДЫ: {e}"
                logger.error("Command failed: %s", e)

            # Язык вывода: явный lang из YAML, иначе авто по расширению
            out_lang = c.lang
            if out_lang == "bash" and c.cmd == "cat":
                out_lang = detect_lang(c.resolved_args, default=c.lang)

            # ДВА блока: команда (bash) + вывод (lang)
            blocks.append(
                f"{heading_prefix} {title_text}\n\n"
                f"```bash\n{prompt}\n```\n"
                f"```{out_lang}\n{output.rstrip()}\n```"
            )

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
