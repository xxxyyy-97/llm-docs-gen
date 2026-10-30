"""Выполнение внешних команд (cat, tree, …)."""
from __future__ import annotations
import os
import subprocess
import shlex
from pathlib import Path


def run(cmd: str, args: list[str], cwd: str | Path) -> str:
    expanded = [os.path.expanduser(a) for a in args]
    line = shlex.join([cmd, *expanded])
    r = subprocess.run(
        line, shell=True,
        capture_output=True, text=True,
        cwd=cwd, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"[{line}] → {r.stderr.strip()}")
    return r.stdout
