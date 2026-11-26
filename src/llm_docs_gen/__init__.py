"""llm-docs-gen: публичный API пакета."""
from .models import CmdArg, ContentItem, DocItem, DocsConfig, ProjectConfig
from .rendering import generate_all, render_item

__all__ = [
    "CmdArg",
    "ContentItem",
    "DocItem",
    "DocsConfig",
    "ProjectConfig",
    "generate_all",
    "render_item",
]
