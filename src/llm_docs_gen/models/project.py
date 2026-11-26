from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from ruamel.yaml import YAML
from .content import ContentItem

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
