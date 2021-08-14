from dataclasses import dataclass
from typing import Annotated

import pytest

from filament import Choices, InvalidChoiceError, from_json


def test_raises_invalid_choice_error_if_field_value_is_not_in_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(acceptable_values)

    @dataclass
    class Spam:
        x: Annotated[int, constraint]

    for num in (-2, 0, 1, 3, 6):
        with pytest.raises(InvalidChoiceError) as exc_info:
            from_json({"x": num}, Spam)
        assert exc_info.value.constraint is constraint
        assert exc_info.value.acceptable_values == acceptable_values


def test_does_not_raise_invalid_choice_error_if_field_value_is_in_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(acceptable_values)

    @dataclass
    class Spam:
        x: Annotated[int, constraint]

    for num in acceptable_values:
        from_json({"x": num}, Spam)


def test_raises_invalid_choice_error_if_field_value_is_not_in_dynamic_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(lambda path: acceptable_values)

    @dataclass
    class Spam:
        x: Annotated[int, constraint]

    for num in (-2, 0, 1, 3, 6):
        with pytest.raises(InvalidChoiceError) as exc_info:
            from_json({"x": num}, Spam)
        assert exc_info.value.constraint is constraint
        assert exc_info.value.acceptable_values == acceptable_values


def test_does_not_raise_invalid_choice_error_if_field_value_is_in_dynamic_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(lambda path: acceptable_values)

    @dataclass
    class Spam:
        x: Annotated[int, constraint]

    for num in acceptable_values:
        from_json({"x": num}, Spam)


def test_raises_invalid_choice_error_if_any_item_within_list_not_in_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(lambda path: acceptable_values)

    @dataclass
    class Spam:
        items: list[Annotated[int, constraint]]

    for numbers in ([1, 4], [5, 6]):
        with pytest.raises(InvalidChoiceError) as exc_info:
            from_json({"items": numbers}, Spam)
        assert exc_info.value.constraint is constraint
        assert exc_info.value.acceptable_values == acceptable_values


def test_does_not_raise_invalid_choice_error_if_all_items_within_list_in_subset():

    acceptable_values = frozenset([2, 4, 5])
    constraint = Choices(lambda path: acceptable_values)

    @dataclass
    class Spam:
        items: list[Annotated[int, constraint]]

    for numbers in ([2, 4], [4, 5], [2, 4, 5]):
        from_json({"items": numbers}, Spam)
