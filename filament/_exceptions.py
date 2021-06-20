from typing import Any, Optional, Type


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
    target_type: Optional[Type]

    def __init__(self, value: Any, target_type: Optional[Type]) -> None:
        if target_type is None:
            type_desc = "None"
        else:
            type_desc = str(target_type)
        super().__init__(
            f"{type_desc} can't be imported from {type(value).__name__}. "
            "Only JSON types, Decimal, date, time, datetime, objects with annotations "
            "or objects implementing the CustomJSONImporter protocol can be imported."
        )
        self.value = value
        self.target_type = target_type


class ValueRequiredError(ValueError):
    """Exception raised when attempting to import None when a not None values was
    required by the type specification.
    """

    target_type: Type

    def __init__(self, target_type: Type) -> None:
        super().__init__(
            f"{target_type.__name__} can't accept a None value, since it is not "
            "Optional"
        )
        self.target_type = target_type


class NoneRequiredError(ValueError):
    """Exception raised when attempting to import a not None value when None was
    required by the type specification.
    """

    value: Any

    def __init__(self, value: Any) -> None:
        super().__init__(f"Received {value}, expected None")
        self.value = value


class UnknownClassTagError(ValueError):
    """Exception raised when trying to import an instance of a
    `~.tagged_class.TaggedClass` using a tag that matches none of the classes in the
    hierarchy.
    """

    target_type: Type
    tag: str

    def __init__(self, target_type: Type, tag: str):
        super().__init__(
            f"{tag} is not a valid class tag for {target_type.__name__}; "
            f"expected one of {', '.join(target_type.filament_tags.keys())}"
        )
        self.target_type = target_type
        self.tag = tag
