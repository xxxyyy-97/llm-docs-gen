from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class CmdArg(BaseModel):
    flag: str | None = None
    value: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> "CmdArg":
        if isinstance(raw, str):
            return cls(value=raw)
        return cls(**raw)
