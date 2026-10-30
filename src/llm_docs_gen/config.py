"""Pydantic-модели для docs.yml."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
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
    cmd: str
    args: list[Any] | str = []   
    title: str | None = None

    @property
    def resolved_args(self) -> list[str]:
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
        # YAML может вернуть вложенный словарь — адаптируем
        return cls(**data)


class ProjectConfig(BaseModel):
    title: str
    path: str
    docs: str
    items: list[DocItem] = Field(default_factory=list) 

    @property
    def sorted_items(self) -> list[DocItem]:
        return sorted(self.items, key=lambda i: i.render)
