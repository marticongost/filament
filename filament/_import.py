from __future__ import annotations

import enum
import json
from abc import abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
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

from ._constraint import Constraint
from ._exceptions import (
    ImportTypeError,
    NoneRequiredError,
    UnknownClassTagError,
    ValueRequiredError,
)
from ._importpath import ImportPath
from ._taggedclass import TaggedClass

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
    value: JSON,
    target_spec: Optional[T],
    *,
    use_custom_importer: bool = True,
    path: Optional[ImportPath] = None,
) -> Optional[T]:
    """Creates an object from its data, expressed as a JSON value.

    The function supports the same types as its complement, `to_json`. Beyond that,
    classes can implement the `CustomJSONImporter` protocol to override the creation
    logic for their instances.

    Args:
        value: JSON value with the data to process.
        target_type: The type of the object to produce.
    """
    if target_spec is None:
        target_type = None
        metadata = None
    else:
        metadata = getattr(target_spec, "__metadata__", None)
        if metadata is None:
            target_type = target_spec
        else:
            target_type = target_spec.__args__[0]

    def get_path() -> ImportPath:
        nonlocal path
        if path is None:
            path = ImportPath(value)
        return path

    def get_value():
        nonlocal target_type

        origin = getattr(target_type, "__origin__", None)
        if target_type and origin is Union:
            for union_type in target_type.__args__:
                try:
                    return from_json(value, union_type, path=path)
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

            if issubclass(target_type, (int, float, str, enum.Enum, Decimal)):
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
                        from_json(
                            k,
                            type_args[0],
                            path=ImportPath(
                                k, parent=get_path(), type=ImportPath.Type.MAPPING_KEY
                            ),
                        ),
                        from_json(
                            v,
                            type_args[1],
                            path=ImportPath(
                                v,
                                parent=get_path(),
                                type=ImportPath.Type.MAPPING_VALUE,
                                key=k,
                            ),
                        ),
                    )
                    for k, v in value.items()
                )  # type: ignore

            if issubclass(target_type, tuple):
                if not isinstance(value, list):
                    raise ImportTypeError(value, target_type)
                return target_type(
                    from_json(
                        v,
                        t,
                        path=ImportPath(
                            v, parent=get_path(), type=ImportPath.Type.TUPLE_ITEM, key=i
                        ),
                    )
                    for i, (v, t) in enumerate(zip(value, type_args))
                )  # type: ignore

            if issubclass(target_type, Collection):
                if not isinstance(value, list):
                    raise ImportTypeError(value, target_type)
                return target_type(
                    from_json(
                        v,
                        type_args[0],
                        path=ImportPath(
                            v,
                            parent=get_path(),
                            type=ImportPath.Type.SEQUENCE_ITEM,
                            key=i,
                        ),
                    )
                    for i, v in enumerate(value)
                )  # type: ignore

        if isinstance(value, dict):
            assert target_type is not None
            cls = target_type
            if issubclass(target_type, TaggedClass):
                class_tag = value.get("class")
                if class_tag:
                    try:
                        cls = target_type.filament_tags[class_tag]  # type: ignore
                    except KeyError:
                        raise UnknownClassTagError(target_type, class_tag)

            annotations = get_type_hints(cls, include_extras=True)
            if annotations:
                values: dict[str, Any] = {}

                for field_name, field_spec in annotations.items():

                    # Skip internal fields set by the library
                    if field_name.startswith("filament_"):
                        continue

                    field_value = value[field_name]
                    field_value = from_json(
                        field_value,
                        field_spec,
                        path=ImportPath(
                            field_value,
                            parent=get_path(),
                            type=ImportPath.Type.FIELD,
                            key=field_name,
                        ),
                    )
                    values[field_name] = field_value

                return cls(**values)

        raise ImportTypeError(value, target_type)

    value = get_value()

    # Apply field constraints
    if metadata is not None:
        path = get_path()
        for annotation in metadata:
            if isinstance(annotation, Constraint):
                annotation.apply(path)

    return value  # type: ignore


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
