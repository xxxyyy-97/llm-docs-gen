def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """Генерирует стандартную Markdown-таблицу."""
    if not headers:
        return ""

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    data_lines = []
    for row in rows:
        safe_row = row[:len(headers)] + [""] * max(0, len(headers) - len(row))
        data_lines.append("| " + " | ".join(safe_row) + " |")

    return "\n".join([header_line, sep_line, *data_lines])


def render_alert(kind: str, body: str) -> str:
    """Генерирует GitHub-style alert: > [!WARNING] + цитата тела."""
    lines = body.strip().splitlines()
    quoted = "\n".join(f"> {line}".rstrip() for line in lines)
    return f"> [!{kind}]\n{quoted}"
