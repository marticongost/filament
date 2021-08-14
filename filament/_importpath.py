from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ImportPath:
    class Type(enum.Enum):
        FIELD = enum.auto()
        MAPPING_KEY = enum.auto()
        MAPPING_VALUE = enum.auto()
        TUPLE_ITEM = enum.auto()
        SEQUENCE_ITEM = enum.auto()

    value: Any
    parent: Optional[ImportPath] = None
    key: Any = None
    type: Optional[Type] = None
