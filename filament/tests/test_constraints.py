from dataclasses import dataclass
from typing import Annotated

import pytest

from filament import Constraint, ConstraintError, ImportPath, from_json


class EvenNumbersConstraint(Constraint):
    def apply(self, path):
        if path.value % 2 != 0:
            raise EvenNumbersConstraintError(self, path)


class EvenNumbersConstraintError(ConstraintError):
    pass


class OddNumbersConstraint(Constraint):
    def apply(self, path):
        if path.value % 2 == 0:
            raise OddNumbersConstraintError(self, path)


class OddNumbersConstraintError(ConstraintError):
    pass


def test_raises_constraint_error_if_constraint_fails():

    even_constraint = EvenNumbersConstraint()
    odd_constraint = OddNumbersConstraint()

    @dataclass
    class Spam:
        x: Annotated[int, even_constraint, odd_constraint]

    with pytest.raises(EvenNumbersConstraintError) as exc_info:
        from_json({"x": 3}, Spam)

    assert exc_info.value.constraint is even_constraint
    assert isinstance(exc_info.value.path, ImportPath)
    assert exc_info.value.path.value == 3

    with pytest.raises(OddNumbersConstraintError) as exc_info:
        from_json({"x": 2}, Spam)

    assert exc_info.value.constraint is odd_constraint
    assert isinstance(exc_info.value.path, ImportPath)
    assert exc_info.value.path.value == 2


def test_does_not_raise_constraint_error_if_constraint_is_satisfied():
    @dataclass
    class Spam:
        x: Annotated[int, EvenNumbersConstraint]

    from_json({"x": 2}, Spam)
