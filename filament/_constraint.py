from abc import ABC, abstractmethod

from ._importpath import ImportPath


class Constraint(ABC):
    """Base class for field constraints."""

    @abstractmethod
    def apply(self, path: ImportPath) -> None:
        """Validates the constraint against the given path.

        If the constraint fails, it raises `ConstraintError` (or a subclass). Otherwise,
        it does nothing.
        """
        pass


class ConstraintError(Exception):
    """An error raised whenever an import constraint is not satisfied when importing an
    object from a JSON document.
    """

    def __init__(self, constraint: Constraint, path: ImportPath):
        super().__init__(f"Can't satisfy constraint {constraint} in {path}")
        self._constraint = constraint
        self._path = path

    @property
    def constraint(self) -> Constraint:
        """The constraint that could not be satisfied."""
        return self._constraint

    @property
    def path(self) -> ImportPath:
        """The path within the JSON document that the constraint was applied to."""
        return self._path
