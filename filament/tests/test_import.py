from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Optional, Type, Union
from unittest.mock import patch

import pytest

from filament import (
    ImportTypeError,
    NoneRequiredError,
    TaggedClass,
    UnknownClassTagError,
    ValueRequiredError,
    from_json,
)


@dataclass(frozen=True)
class FromJsonCall:
    value: Any
    target_type: Type


def test_imports_none_as_none():
    assert from_json(None, type(None)) is None


def test_raises_exception_when_importing_none_on_non_optional_type():
    with pytest.raises(ValueRequiredError):
        from_json(None, int)


def test_raises_exception_when_importing_value_on_none_type():
    with pytest.raises(NoneRequiredError):
        from_json(5, None)


def test_imports_none_as_none_on_optional_type():
    assert from_json(None, Optional[int]) is None


def test_imports_value_as_value_on_optional_type():
    assert from_json(5, Optional[int]) == 5


def test_imports_int_as_int():
    assert from_json(0, int) == 0
    assert from_json(1, int) == 1
    assert from_json(-123, int) == -123
    assert from_json(100000, int) == 100000


def test_imports_float_as_float():
    assert from_json(0.0, float) == 0.0
    assert from_json(1.5, float) == 1.5
    assert from_json(-123.235, float) == -123.235
    assert from_json(0.123891234123, float) == 0.123891234123


def test_imports_true_as_true():
    assert from_json(True, bool) is True


def test_imports_false_as_false():
    assert from_json(False, bool) is False


def test_imports_str_as_str():
    assert from_json("", str) == ""
    assert from_json("Hello world", str) == "Hello world"


def test_recursively_imports_lists():
    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        assert from_json([1, 2, 3], list[int]) == [
            FromJsonCall(1, int),
            FromJsonCall(2, int),
            FromJsonCall(3, int),
        ]


def test_recursively_imports_list_subclass():
    class TestList(list):
        pass

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json([1, 2, 3], TestList[int])
        assert isinstance(obj, TestList)
        assert obj == TestList(
            [
                FromJsonCall(1, int),
                FromJsonCall(2, int),
                FromJsonCall(3, int),
            ]
        )


def test_recursively_imports_sets():
    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        assert from_json([1, 2, 3], set[int]) == {
            FromJsonCall(1, int),
            FromJsonCall(2, int),
            FromJsonCall(3, int),
        }


def test_recursively_imports_set_subclass():
    class TestSet(set):
        pass

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json([1, 2, 3], TestSet[int])
        assert isinstance(obj, TestSet)
        assert obj == TestSet(
            [
                FromJsonCall(1, int),
                FromJsonCall(2, int),
                FromJsonCall(3, int),
            ]
        )


def test_recursively_imports_dicts():
    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        assert from_json({"a": 1, "b": 2, "c": 3}, dict[str, int]) == {
            FromJsonCall("a", str): FromJsonCall(1, int),
            FromJsonCall("b", str): FromJsonCall(2, int),
            FromJsonCall("c", str): FromJsonCall(3, int),
        }


def test_recursively_imports_dict_subclass():
    class TestDict(dict):
        pass

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json({"a": 1, "b": 2, "c": 3}, TestDict[str, int])
        assert isinstance(obj, TestDict)
        assert obj == TestDict(
            {
                FromJsonCall("a", str): FromJsonCall(1, int),
                FromJsonCall("b", str): FromJsonCall(2, int),
                FromJsonCall("c", str): FromJsonCall(3, int),
            }
        )


def test_imports_decimal_from_str():
    assert from_json("0", Decimal) == Decimal("0")
    assert from_json("1.000", Decimal) == Decimal("1.000")
    assert from_json("-13.75323", Decimal) == Decimal("-13.75323")


def test_imports_enum():
    class TestEnum(Enum):
        A = 1
        B = 2
        C = 3

    assert from_json(1, TestEnum) is TestEnum.A
    assert from_json(2, TestEnum) is TestEnum.B
    assert from_json(3, TestEnum) is TestEnum.C


def test_imports_date_from_iso_str():
    d = date.today()
    assert from_json(d.isoformat(), date) == d


def test_imports_datetime_from_iso_str():
    dt = datetime.now()
    assert from_json(dt.isoformat(), datetime) == dt


def test_imports_time_from_iso_str():
    t = datetime.now().time()
    assert from_json(t.isoformat(), time) == t


def test_supports_custom_json_importer_protocol():
    class TestObject:
        def __init__(self, value):
            self.value = value

        @classmethod
        def from_json(cls, value):
            return cls(value + "!")

    obj = from_json("Hello", TestObject)
    assert isinstance(obj, TestObject)
    assert obj.value == "Hello!"


def test_can_override_import_protocol_on_int_subclasses():
    class TestInt(int):
        @classmethod
        def from_json(cls, value):
            return cls(value / 100)

    obj = from_json(300, TestInt)
    assert isinstance(obj, TestInt)
    assert obj == TestInt(3)


def test_can_override_import_protocol_on_float_subclasses():
    class TestFloat(float):
        @classmethod
        def from_json(cls, value):
            return cls(value)

    obj = from_json("3.5", TestFloat)
    assert isinstance(obj, TestFloat)
    assert obj == TestFloat(3.5)


def test_can_override_export_protocol_on_str_subclasses():
    class TestStr(str):
        @classmethod
        def from_json(cls, value):
            return cls(value.strip())

    obj = from_json("  Hello world  ", TestStr)
    assert isinstance(obj, TestStr)
    assert obj == TestStr("Hello world")


def test_imports_object_with_type_hints_from_dict():
    class TestObject:
        num: int
        text: str

        def __init__(self, num, text):
            self.num = num
            self.text = text

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json({"num": 1, "text": "foobar"}, TestObject)
        assert isinstance(obj, TestObject)
        assert obj.num == FromJsonCall(1, int)
        assert obj.text == FromJsonCall("foobar", str)


def test_imports_object_with_annotated_type_hints_from_dict():
    class TestObject:
        num: Annotated[int, "foobar"]
        text: str

        def __init__(self, num, text):
            self.num = num
            self.text = text

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json({"num": 1, "text": "foobar"}, TestObject)
        assert isinstance(obj, TestObject)
        assert obj.num == FromJsonCall(1, int)
        assert obj.text == FromJsonCall("foobar", str)


def test_imports_dataclass_instance_from_dict():
    @dataclass
    class TestObject:
        num: int
        text: str

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json({"num": 1, "text": "foobar"}, TestObject)
        assert isinstance(obj, TestObject)
        assert obj.num == FromJsonCall(1, int)
        assert obj.text == FromJsonCall("foobar", str)


def test_imports_frozen_dataclass_instance_from_dict():
    @dataclass(frozen=True)
    class TestObject:
        num: int
        text: str

    with patch("filament._import.from_json") as MockClass:
        MockClass.side_effect = FromJsonCall
        obj = from_json({"num": 1, "text": "foobar"}, TestObject)
        assert isinstance(obj, TestObject)
        assert obj.num == FromJsonCall(1, int)
        assert obj.text == FromJsonCall("foobar", str)


def test_raises_error_when_importing_an_unsupported_type():
    class TestObject:
        pass

    with pytest.raises(ImportTypeError):
        from_json({}, TestObject)


def test_can_import_unions():
    assert from_json(5, Union[int, str]) == 5
    assert from_json(5, Union[str, int]) == "5"
    assert from_json("5", Union[int, str]) == 5
    assert from_json("5", Union[str, int]) == "5"
    assert from_json("5.3", Union[int, float, str]) == 5.3
    assert from_json("5.3", Union[int, str, float]) == "5.3"
    assert from_json("foobar", Union[int, str]) == "foobar"


def test_raises_error_when_no_union_type_matches():
    with pytest.raises(ImportTypeError):
        assert from_json("foobar", Union[int, datetime])


def test_can_discriminate_tagged_classes():
    @dataclass
    class A(TaggedClass):
        a: str

    @dataclass
    class B(A):
        b: str

    @dataclass
    class C(A):
        c: str

    @dataclass
    class D(B):
        d: str

    assert from_json({"class": "A", "a": "a"}, A) == A(a="a")
    assert from_json({"class": "B", "a": "a", "b": "b"}, A) == B(a="a", b="b")
    assert from_json({"class": "C", "a": "a", "c": "c"}, A) == C(a="a", c="c")
    assert (
        from_json(
            {
                "class": "D",
                "a": "a",
                "b": "b",
                "d": "d",
            },
            A,
        )
        == D(a="a", b="b", d="d")
    )


def test_assumes_root_class_when_importing_tagged_classes_with_tag_missing():
    @dataclass
    class A(TaggedClass):
        a: str

    @dataclass
    class B(A):
        b: str

    assert from_json({"a": "a"}, A) == A(a="a")
    assert from_json({"a": "a", "b": "b"}, A) == A(a="a")
    assert from_json({"a": "a", "b": "b"}, B) == B(a="a", b="b")


def test_raises_exception_when_importing_tagged_class_with_unknown_tag():
    @dataclass
    class A(TaggedClass):
        a: str

    @dataclass
    class B(A):
        b: str

    with pytest.raises(UnknownClassTagError):
        from_json({"class": "C", "a": "a"}, A)
