from pydantic import BaseModel, Field, model_validator
from typing import Any, Literal
from .base import CmdArg

class ContentItem(BaseModel):
    """
    Элемент контента: command | table | text | alert.

    Примеры YAML:
      # Команда
      - cmd: cat
        args: file.txt

      # Таблица
      - type: table
        headers: ["Name", "Port"]
        rows: [["pg_dwh", "5432"]]

      # Текст
      - type: text
        title: Примечание
        body: ...

      # Алерт
      - type: alert
        alert: WARNING
        title: Не редактируйте вручную
        body: Файл генерируется автоматически.
    """

    # ── Поле типа ──
    type: Literal["command", "table", "text", "alert"] = "command"

    # ── Для команд ──
    cmd: str | None = None
    args: list[Any] | str = []

    # ── Общие поля ──
    title: str | None = None
    title_level: int = Field(default=2, ge=1, le=6)

    # ── Для таблиц ──
    headers: list[str] | None = None
    rows: list[list[str]] | None = None

    # ── Для текста и алертов ──
    body: str | None = None

    # ── НОВОЕ: вид алерта ──
    alert: Literal["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"] = "NOTE"

    # ── НОВОЕ: язык блока вывода команды ──
    # bash | yaml | sql | json | toml | python | dockerfile | text | ...
    lang: str = "bash"

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

        elif self.type in ("text", "alert"):
            if self.body is None:
                raise ValueError(f"Поле 'body' обязательно для type='{self.type}'")

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

