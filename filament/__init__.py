import json
from abc import abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from types import FunctionType
from typing import Any, Collection, Mapping, Optional, Protocol, Type, TypeVar, Union

JSON = Union[None, str, bool, int, float, dict[str, Any], list]

M = TypeVar("M", bound="CustomJSONImporter")
T = TypeVar("T")


class CustomJSONExporter(Protocol):
    """Protocol that can be implemented by classes wanting to specify the behavior of
    the `to_json` function.
    """

    @abstractmethod
    def to_json(self) -> JSON:
        ...


class CustomJSONImporter(Protocol):
    """Protocol that can be implemented by classes wanting to specify the behavior of
    the `from_json` function.
    """

    @classmethod
    @abstractmethod
    def from_json(self, data: JSON) -> M:
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
        annotations = getattr(type(value), "__annotations__", None)
        if annotations:
            return {
                field_name: to_json(getattr(value, field_name))
                for field_name, __ in annotations.items()
            }

    raise ExportTypeError(value)


def from_json(
    value: JSON, target_type: T, *, use_custom_importer: bool = True
) -> Optional[T]:
    """Creates an object from its data, expressed as a JSON value.

    The function supports the same types as its complement, `to_json`. Beyond that,
    classes can implement the `CustomJSONImporter` protocol to override the creation
    logic for their instances.

    Args:
        value: JSON value with the data to process.
        target_type: The type of the object to produce.
    """
    if value is None:
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
        annotations = getattr(target_type, "__annotations__", None)
        if annotations:
            return target_type(
                **{
                    field_name: from_json(value[field_name], field_type)
                    for field_name, field_type in annotations.items()
                }
            )

    raise ImportTypeError(value, target_type)


def dumps(value: Any, **kwargs) -> str:
    """Serializes the given value to a JSON string.

    Args:
        value: The value to serialize.
        kwargs: Keyword parameters to forward to `json.dumps`

    Returns:
        A JSON string representing the value.
    """
    return json.dumps(to_json(value), **kwargs)


def loads(json_str: str, type: Optional[T] = None, **kwargs) -> Optional[T]:
    """Deserializes a value from a JSON string.

    Args:
        json_str: The JSON string to deserialize.
        type: The type of the value described by the string.
        kwargs: Keyword parameters to forward to `json.loads`

    Returns:
        The value described by the JSON string.
    """
    return from_json(loads(json_str, **kwargs), type)


class ExportTypeError(TypeError):
    """Exception raised when attempting to export an object of an unsupported type to
    JSON.

    The exception will be raised whenever `to_json` or `dumps` are called with a value
    of a type that filament doesn't know how to export to JSON.
    """

    value: Any

    def __init__(self, value: Any) -> None:
        super().__init__(
            f"{type(value).__name__} can't be exported to JSON. Only JSON types, "
            "Decimal, date, time, datetime, objects with annotations or objects "
            "implementing the CustomJSONExporter protocol can be exported."
        )
        self.value = value


class ImportTypeError(TypeError):
    """Exception raised when attempting to import an object of an unsupported type from
    JSON.

    The exception will be raised whenever `from_json` or `loads` are called with a
    target type that filament doesn't know how to import from JSON.
    """

    value: Any
    target_type: Type

    def __init__(self, value: Any, target_type: Type) -> None:
        super().__init__(
            f"{target_type.__name__} can't be imported from {type(value).__name__}. "
            "Only JSON types, Decimal, date, time, datetime, objects with annotations "
            "or objects implementing the CustomJSONImporter protocol can be imported."
        )
        self.value = value
        self.target_type = target_type
