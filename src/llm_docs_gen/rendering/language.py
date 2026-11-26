from pathlib import Path
# Автоопределение языка по расширению файла (если lang не задан явно)
_EXT_LANG: dict[str, str] = {
    ".yml": "yaml", ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".sql": "sql",
    ".py": "python",
    ".sh": "bash",
    ".env": "bash",
    ".example": "bash",
    ".csv": "text",
    ".md": "markdown",
}

def detect_lang(args: list[str], default: str = "bash") -> str:
    """Определяет язык блока по расширению первого файла в аргументах."""
    for a in args:
        name = Path(a).name.lower()
        if name.startswith("dockerfile") or ".dockerfile" in name:
            return "dockerfile"
        suffix = Path(name).suffix
        if suffix in _EXT_LANG:
            return _EXT_LANG[suffix]
    return default
