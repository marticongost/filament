from __future__ import annotations

from typing import Optional, Type


class TaggedClass:
    """Mixin that simplifies the serialization and deserialization of instances of a
    a class hierarchy.
    """

    filament_tag: str
    filament_tags: Optional[dict[str, Type[TaggedClass]]] = None

    def __init_subclass__(cls, filament_tag: Optional[str] = None, **kwargs) -> None:

        super().__init_subclass__()

        if cls.filament_tags is None:
            cls.filament_tags = {}

        cls.filament_tag = filament_tag or cls.__name__

        try:
            existing_class = cls.filament_tags[cls.filament_tag]
        except KeyError:
            pass
        else:
            raise TypeError(
                f"{existing_class.__module__}.{existing_class.__name__} and "
                f"{cls.__module__}.{cls.__name__} have the same tag "
                f"({cls.filament_tag}); either rename one of the classes, or set an "
                "explicit tag with the filament_tag initialization parameter"
            )

        cls.filament_tags[cls.filament_tag] = cls
