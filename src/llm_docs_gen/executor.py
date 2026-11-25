"""Выполнение внешних команд (cat, tree, awk, …)."""
from __future__ import annotations
import os
import subprocess
import shlex
import glob as py_glob  # ← Стандартная библиотека для раскрытия * ? []
from pathlib import Path


def run(cmd: str, args: list[str], cwd: str | Path) -> str:
    """
    Выполняет команду, раскрывая ~ и glob-паттерны (*, ?, []).
    Важно: glob раскрывается относительно директории cwd,
    чтобы пути в docs.yml работали предсказуемо независимо от того,
    откуда запущен генератор.
    """
    base_dir = str(Path(cwd).expanduser())
    expanded_args: list[str] = []

    for a in args:
        # 1. Раскрываем домашнюю директорию (~)
        path_str = os.path.expanduser(a)

        # 2. Проверяем наличие спецсимволов glob
        if any(char in path_str for char in ['*', '?', '[']):
            # Разрешаем glob относительно рабочей директории проекта
            # root_dir гарантирует, что './folder/*' ищет именно там
            matches = py_glob.glob(path_str, root_dir=base_dir)

            if matches:
                # Сортируем для стабильности вывода документации
                expanded_args.extend(sorted(matches))
            else:
                # Если совпадений нет — оставляем исходный путь.
                # Команда упадет с понятной ошибкой "No such file or directory",
                # вместо тихого игнорирования пустого списка.
                expanded_args.append(path_str)
        else:
            # Обычный путь без спецсимволов
            expanded_args.append(path_str)

    # 3. Формируем финальную строку команды
    # shlex.join корректно экранирует пробелы в именах файлов,
    # но уже НЕ кавычит наши раскрытые пути, так как они стали обычными строками.
    line = shlex.join([cmd, *expanded_args])

    r = subprocess.run(
        line, shell=True,
        capture_output=True, text=True,
        cwd=cwd, timeout=60,
    )

    if r.returncode != 0:
        raise RuntimeError(f"[{line}] → {r.stderr.strip()}")
    output = r.stdout
    # Замена NBSP (U+00A0) на обычный пробел (U+0020)
    # Также можно заменить другие редкие whitespace, если нужно
    output = output.replace('\u00a0', ' ')
    return output
