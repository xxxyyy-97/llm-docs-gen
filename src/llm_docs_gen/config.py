from __future__ import annotations
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator
from ruamel.yaml import YAML


class CmdArg(BaseModel):
    """Аргумент команды: либо {'flag': 'a'}, либо {'value': '...'}.
    В YAML встречается и строка напрямую."""
    flag: str | None = None
    value: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> "CmdArg":
        if isinstance(raw, str):
            return cls(value=raw)
        return cls(**raw)


class ContentItem(BaseModel):
    """
    Элемент контента. Может быть командой (command), таблицей (table) или текстом (text).

    Примеры YAML:
      # Команда (по умолчанию)
      - cmd: cat
        args: file.txt

      # Таблица
      - type: table
        title: Сервисы
        headers: ["Name", "Port"]
        rows:
          - ["pg_dwh", "5432"]

      # Текст
      - type: text
        title: Важное примечание
        body: |
          Этот файл генерируется автоматически.
          Не редактируйте его вручную!
    """

    # ── Поле типа ──
    type: Literal["command", "table", "text"] = "command"

    # ── Для команд ──
    cmd: str | None = None
    args: list[Any] | str = []

    # ── Общие поля ──
    title: str | None = None

    # ── Для таблиц ──
    headers: list[str] | None = None
    rows: list[list[str]] | None = None

    # ── НОВОЕ ПОЛЕ ДЛЯ ТЕКСТА ──
    body: str | None = None

    @model_validator(mode="after")
    def validate_content_type(self) -> "ContentItem":
        """Проверяет корректность заполнения полей в зависимости от типа."""

        if self.type == "command":
            if not self.cmd:
                raise ValueError("Поле 'cmd' обязательно для type='command'")

        elif self.type == "table":
            if self.headers is None or self.rows is None:
                raise ValueError("Поля 'headers' и 'rows' обязательны для type='table'")
            if len(self.headers) == 0:
                raise ValueError("'headers' не может быть пустым списком")

            expected_cols = len(self.headers)
            for i, row in enumerate(self.rows):
                if len(row) != expected_cols:
                    raise ValueError(
                        f"Строка {i} имеет {len(row)} колонок, ожидалось {expected_cols}"
                    )

        elif self.type == "text":
            if self.body is None:
                raise ValueError("Поле 'body' обязательно для type='text'")

        return self

    @property
    def resolved_args(self) -> list[str]:
        """Разрешает аргументы команды в плоский список строк."""
        if self.type != "command" or not self.cmd:
            return []

        raw = [self.args] if isinstance(self.args, str) else self.args
        out: list[str] = []
        for a in raw:
            arg = CmdArg.parse(a)
            if arg.flag is not None:
                out.append(f"-{arg.flag}")
            if arg.value is not None:
                out.append(arg.value)
        return out


class DocItem(BaseModel):
    item: str
    render: int
    file: str
    description: str | None = None
    content: list[ContentItem] = []


class DocsConfig(BaseModel):
    version: str | None = None
    project: dict[str, Any] | None = None

    @classmethod
    def load(cls, path: Path | str) -> "DocsConfig":
        yaml = YAML()
        with open(path) as f:
            data = yaml.load(f)
        return cls(**data)


class ProjectConfig(BaseModel):
    title: str
    path: str
    docs: str
    items: list[DocItem] = Field(default_factory=list)

    @property
    def sorted_items(self) -> list[DocItem]:
        return sorted(self.items, key=lambda i: i.render)
