from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any
from unittest.mock import patch

import pytest

from filament import ExportTypeError, TaggedClass, to_json


@dataclass(frozen=True)
class ToJsonCall:
    value: Any


def test_exports_none_as_none():
    assert to_json(None) is None


def test_exports_int_as_int():
    assert to_json(0) == 0
    assert to_json(1) == 1
    assert to_json(-123) == -123
    assert to_json(100000) == 100000


def test_exports_float_as_float():
    assert to_json(0.0) == 0.0
    assert to_json(1.5) == 1.5
    assert to_json(-123.235) == -123.235
    assert to_json(0.123891234123) == 0.123891234123


def test_exports_true_as_true():
    assert to_json(True) is True


def test_exports_false_as_false():
    assert to_json(False) is False


def test_exports_str_as_str():
    assert to_json("") == ""
    assert to_json("Hello world") == "Hello world"


def test_recursively_exports_list_as_list():
    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        assert to_json([1, 2, 3]) == [ToJsonCall(1), ToJsonCall(2), ToJsonCall(3)]


def test_recursively_exports_set_as_list():
    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        assert to_json({1, 2, 3}) == [ToJsonCall(1), ToJsonCall(2), ToJsonCall(3)]


def test_recursively_exports_dict_as_dict():
    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        assert to_json({"a": 1, "b": 2, "c": 3}) == {
            ToJsonCall("a"): ToJsonCall(1),
            ToJsonCall("b"): ToJsonCall(2),
            ToJsonCall("c"): ToJsonCall(3),
        }


def test_exports_decimal_as_str():
    assert to_json(Decimal("0")) == "0"
    assert to_json(Decimal("1.000")) == "1.000"
    assert to_json(Decimal("-13.75323")) == "-13.75323"


def test_exports_enum_as_value_str():
    class TestEnum(Enum):
        A = 1
        B = 2
        C = 3

    assert to_json(TestEnum.A) == 1
    assert to_json(TestEnum.B) == 2
    assert to_json(TestEnum.C) == 3


def test_exports_date_as_iso_str():
    d = date.today()
    assert to_json(d) == d.isoformat()


def test_exports_datetime_as_iso_str():
    dt = datetime.now()
    assert to_json(dt) == dt.isoformat()


def test_exports_time_as_iso_str():
    t = datetime.now().time()
    assert to_json(t) == t.isoformat()


def test_supports_custom_json_exporter_protocol():
    class TestObject:
        def __init__(self, value):
            self.value = value

        def to_json(self):
            return self.value + "!"

    assert to_json(TestObject("Hello")) == "Hello!"


def test_can_override_export_protocol_on_int_subclasses():
    class TestInt(int):
        def to_json(self):
            return int(self) * 100

    assert to_json(TestInt(3)) == 300


def test_can_override_export_protocol_on_float_subclasses():
    class TestFloat(float):
        def to_json(self):
            return str(self)

    assert to_json(TestFloat(3.5)) == "3.5"


def test_can_override_export_protocol_on_str_subclasses():
    class TestStr(str):
        def to_json(self):
            return self + "!"

    assert to_json(TestStr("yay")) == "yay!"


def test_exports_object_with_type_hints_as_dict():
    class TestObject:
        x: int
        y: int

    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        obj = TestObject()
        obj.x = 1
        obj.y = 2
        assert to_json(obj) == {"x": ToJsonCall(1), "y": ToJsonCall(2)}


def test_exports_object_with_annotated_type_hints_as_dict():
    class TestObject:
        x: Annotated[int, "foobar"]
        y: int

    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        obj = TestObject()
        obj.x = 1
        obj.y = 2
        assert to_json(obj) == {"x": ToJsonCall(1), "y": ToJsonCall(2)}


def test_exports_dataclass_instance_as_dict():
    @dataclass
    class TestObject:
        x: int
        y: int

    with patch("filament._export.to_json") as MockClass:
        MockClass.side_effect = ToJsonCall
        obj = TestObject(x=1, y=2)
        assert to_json(obj) == {"x": ToJsonCall(1), "y": ToJsonCall(2)}


def test_raises_error_when_exporting_an_unsupported_type():
    class TestObject:
        pass

    with pytest.raises(ExportTypeError):
        to_json(TestObject())


def test_raises_error_when_exporting_a_function():
    def foobar():
        pass

    with pytest.raises(ExportTypeError):
        to_json(foobar)


def test_raises_error_when_exporting_a_class():
    class TestObject:
        pass

    with pytest.raises(ExportTypeError):
        to_json(TestObject)


def test_exports_tagged_classes():
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

    assert to_json(A(a="a")) == {"class": "A", "a": "a"}
    assert to_json(B(a="a", b="b")) == {"class": "B", "a": "a", "b": "b"}
    assert to_json(C(a="a", c="c")) == {"class": "C", "a": "a", "c": "c"}
    assert to_json(D(a="a", b="b", d="d")) == {
        "class": "D",
        "a": "a",
        "b": "b",
        "d": "d",
    }


def test_tagged_classes_can_override_their_tag_name():
    @dataclass
    class A(TaggedClass):
        a: str

    @dataclass
    class B(A, filament_tag="foobar"):
        b: str

    assert to_json(A(a="a")) == {"class": "A", "a": "a"}
    assert to_json(B(a="a", b="b")) == {"class": "foobar", "a": "a", "b": "b"}


def test_maintains_one_class_tag_mapping_per_class_hierarchy():
    class A(TaggedClass):
        pass

    class B(A):
        pass

    class X(TaggedClass):
        pass

    class Y(X):
        pass

    assert B.filament_tags is A.filament_tags
    assert A.filament_tags == {"A": A, "B": B}

    assert X.filament_tags is Y.filament_tags
    assert X.filament_tags == {"X": X, "Y": Y}
