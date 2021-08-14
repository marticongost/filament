from typing import Callable, Generic, Hashable, Iterable, TypeVar, Union

from ._constraint import Constraint, ConstraintError
from ._importpath import ImportPath

T = TypeVar("T", bound=Hashable)


class Choices(Generic[T], Constraint):
    """An import constraint that limits the values that are accepted by a specific path
    within the imported object graph to a closed set of options.
    """

    def __init__(self, values: Union[Iterable[T], Callable[[ImportPath], Iterable[T]]]):
        if not callable(values) and not isinstance(values, frozenset):
            values = frozenset(values)
        self._values = values

    def apply(self, path: ImportPath) -> None:
        acceptable_values = self.values(path)
        if path.value not in acceptable_values:
            raise InvalidChoiceError(self, path, acceptable_values)

    def values(self, path: ImportPath) -> frozenset[T]:
        """Obtains the values that are acceptable for the given path."""
        if callable(self._values):
            return frozenset(self._values(path))
        return self._values


class InvalidChoiceError(Generic[T], ConstraintError):
    """An error raised whenever a `Choices` constraint is not satisfied when importing
    an object from a JSON document.
    """

    def __init__(
        self, constraint: Choices, path: ImportPath, acceptable_values: frozenset[T]
    ):
        super().__init__(constraint, path)
        self._acceptable_values = acceptable_values

    @property
    def acceptable_values(self) -> frozenset[T]:
        """The set of values that would have been acceptable."""
        return self._acceptable_values
