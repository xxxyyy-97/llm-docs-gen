"""CLI: llm-docs-gen --config docs.yml"""
from __future__ import annotations
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console

from .config import DocsConfig, ProjectConfig
from .renderer import generate_all

app = typer.Typer()
console = Console()


@app.command()
def main(
    config: Path = typer.Option("docs.yml", "--config", "-c", help="Путь к docs.yml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод команд"),
):
    # 1. Получаем логгер нашего пакета
    logger = logging.getLogger("llm_docs_gen")
    
    # 2. Устанавливаем уровень глобально для этого пакета
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING) # Или INFO, если хотите видеть ошибки
        
    # 3. Настраиваем форматирование ТОЛЬКО если еще нет обработчиков
    # (чтобы не дублировать логи при повторных вызовах или тестах)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter("%(asctime)s [%(levelname)-5s] %(name)s: %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    # Отключаем propagate, чтобы сообщения не дублировались в root logger
    logger.propagate = False
    """Генерация markdown-документации из docs.yml."""
    cfg = DocsConfig.load(config)
    if cfg.project is None:
        raise ValueError("В docs.yml отсутствует секция 'project'")
    proj = ProjectConfig(**cfg.project)
    files = generate_all(proj)
    for f in files:
        console.print(f"  [green]✓[/green] {f}")
    console.print(f"\n[bold]{len(files)} файлов создано.[/bold]")


if __name__ == "__main__":
    app()
