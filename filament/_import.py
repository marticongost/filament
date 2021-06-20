import json
from abc import abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Collection,
    Mapping,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

from ._exceptions import ImportTypeError, NoneRequiredError, ValueRequiredError

JSON = Union[None, str, bool, int, float, dict[str, Any], list]

M = TypeVar("M", bound="CustomJSONImporter")
T = TypeVar("T", bound=Type)


class CustomJSONImporter(Protocol):
    """Protocol that can be implemented by classes wanting to specify the behavior of
    the `from_json` function.
    """

    @classmethod
    @abstractmethod
    def from_json(self, data: JSON) -> M:
        ...


def from_json(
    value: JSON, target_type: Optional[T], *, use_custom_importer: bool = True
) -> Optional[T]:
    """Creates an object from its data, expressed as a JSON value.

    The function supports the same types as its complement, `to_json`. Beyond that,
    classes can implement the `CustomJSONImporter` protocol to override the creation
    logic for their instances.

    Args:
        value: JSON value with the data to process.
        target_type: The type of the object to produce.
    """
    origin = getattr(target_type, "__origin__", None)
    if target_type and origin is Union:
        for union_type in target_type.__args__:
            try:
                return from_json(value, union_type)
            except (TypeError, ValueError):
                pass
        raise ImportTypeError(value, target_type)
    elif target_type in (None, None.__class__):
        if value is not None:
            raise NoneRequiredError(value)
        return None
    elif value is None:
        if target_type is not None:
            raise ValueRequiredError(target_type)
        return None

    if use_custom_importer:
        custom_importer = getattr(target_type, "from_json", None)
        if custom_importer:
            return custom_importer(value)

    original_type = getattr(target_type, "__origin__", None)
    type_args = getattr(target_type, "__args__", None)

    if original_type:
        target_type = original_type
    else:
        assert isinstance(target_type, type)

        if issubclass(target_type, (int, float, str, Enum, Decimal)):
            return target_type(value)  # type: ignore

        if issubclass(target_type, (date, time, datetime)):
            return target_type.fromisoformat(value)  # type: ignore

    if type_args:
        assert isinstance(target_type, type)

        if issubclass(target_type, Mapping):
            if not isinstance(value, Mapping):
                raise ImportTypeError(value, target_type)
            return target_type(
                (
                    from_json(k, type_args[0]),
                    from_json(v, type_args[1]),
                )
                for k, v in value.items()
            )  # type: ignore

        if issubclass(target_type, tuple):
            if not isinstance(value, list):
                raise ImportTypeError(value, target_type)
            return target_type(from_json(v, t) for v, t in zip(value, type_args))  # type: ignore

        if issubclass(target_type, Collection):
            if not isinstance(value, list):
                raise ImportTypeError(value, target_type)
            return target_type(from_json(v, type_args[0]) for v in value)  # type: ignore

    if isinstance(value, dict):
        annotations = get_type_hints(target_type)
        if annotations:
            return target_type(
                **{
                    field_name: from_json(value[field_name], field_type)
                    for field_name, field_type in annotations.items()
                }
            )  # type: ignore

    raise ImportTypeError(value, target_type)


def loads(json_str: str, type: Optional[T] = None, **kwargs) -> Optional[T]:
    """Deserializes a value from a JSON string.

    Args:
        json_str: The JSON string to deserialize.
        type: The type of the value described by the string.
        kwargs: Keyword parameters to forward to `json.loads`

    Returns:
        The value described by the JSON string.
    """
    return from_json(json.loads(json_str, **kwargs), type)
