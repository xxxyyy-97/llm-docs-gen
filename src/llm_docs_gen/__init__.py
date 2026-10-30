"""llm-docs-gen: генератор документации для LLM из docs.yml."""
from .config import DocsConfig, ProjectConfig
from .renderer import generate_all, render_item

__all__ = ["DocsConfig", "ProjectConfig", "generate_all", "render_item"]   
