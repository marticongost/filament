import json
from abc import abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from types import FunctionType
from typing import Any, Collection, Mapping, Protocol, Type, TypeVar, get_type_hints

from ._exceptions import ExportTypeError
from ._taggedclass import TaggedClass
from ._types import JSON

T = TypeVar("T", bound=Type)


class CustomJSONExporter(Protocol):
    """Protocol that can be implemented by classes wanting to specify the behavior of
    the `to_json` function.
    """

    @abstractmethod
    def to_json(self) -> JSON:
        ...


def to_json(value: Any, *, use_custom_exporter: bool = True) -> JSON:
    """Converts a value into a value apt for JSON serialization.

    Out of the box, filament can convert the following types automatically:

        - All JSON scalar types (`str`, `int`, `float`, `bool`, `None`)
        - `Decimal`
        - `Enum`
        - `date`, `time`, `datetime`
        - Collections containing any of the supported types
        - Mappings with string keys and values consisting of any of the supported types
        - Objects with class level type hints for their attributes (including instances
          of a dataclass)

    Beyond this, objects can implement or customize their conversion by implementing the
    `CustomJSONExporter` protocol.

    Args:
        value: The value to convert.
        use_custom_exporter: If set to `False`, the `CustomJSONExporter` protocol will
            be disabled for this value. This is useful when implementing the protocol;
            it allows the custom implementation to call the default implementation,
            without triggering an infinite recursion loop.

    Returns:
        The converted value.
    """
    if value is None:
        return None

    if use_custom_exporter:
        custom_exporter = getattr(value, "to_json", None)
        if custom_exporter is not None:
            return custom_exporter()

    if isinstance(value, (str, int, float)):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (time, date, datetime)):
        return value.isoformat()

    if isinstance(value, Mapping):
        record = {}
        for k, v in value.items():
            k = to_json(k)
            record[k] = to_json(v)

        return record

    if isinstance(value, Collection):
        return [to_json(v) for v in value]

    if not isinstance(value, FunctionType):
        annotations = get_type_hints(type(value))
        if annotations:
            data = {
                field_name: to_json(getattr(value, field_name))
                for field_name, __ in annotations.items()
                if not field_name.startswith("filament_")
            }
            if isinstance(value, TaggedClass):
                data["class"] = value.filament_tag
            return data

    raise ExportTypeError(value)


def dumps(value: Any, **kwargs) -> str:
    """Serializes the given value to a JSON string.

    Args:
        value: The value to serialize.
        kwargs: Keyword parameters to forward to `json.dumps`

    Returns:
        A JSON string representing the value.
    """
    return json.dumps(to_json(value), **kwargs)
