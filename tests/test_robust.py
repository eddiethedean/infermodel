"""Robust tests: edge cases, validation behavior, invalid input, schema shapes."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from infermodel import infer_schema, infer_model, InferConfig
from infermodel.emit_pydantic import model_from_schema
from infermodel.schema import get_fields


# ---- Empty and minimal input ----

def test_infer_schema_empty_list() -> None:
    """Empty list of rows yields schema with no fields."""
    schema = infer_schema([])
    assert schema["type"] == "model"
    assert schema["fields"] == {}


def test_infer_schema_single_row() -> None:
    """Single row: all fields required, no nullable unless value is None."""
    schema = infer_schema([{"a": 1, "b": "x"}])
    assert schema["fields"]["a"]["type"] == "int"
    assert schema["fields"]["a"]["required"] is True
    assert schema["fields"]["b"]["type"] == "str"
    assert schema["fields"]["b"]["required"] is True


def test_infer_schema_single_row_with_none() -> None:
    """Single row with None makes that field nullable; type is any when only evidence is None."""
    schema = infer_schema([{"id": 1, "name": None}])
    assert schema["fields"]["name"]["nullable"] is True
    assert schema["fields"]["name"]["type"] == "any"


def test_infer_schema_empty_dicts() -> None:
    """List of empty dicts yields empty fields."""
    schema = infer_schema([{}, {}, {}])
    assert schema["type"] == "model"
    assert schema["fields"] == {}


def test_infer_schema_all_none_in_column() -> None:
    """Column where every value is None: nullable True, type any."""
    schema = infer_schema([{"x": None}, {"x": None}])
    assert schema["fields"]["x"]["nullable"] is True
    assert schema["fields"]["x"]["type"] == "any"


# ---- Validation: inferred model accepts valid and rejects invalid ----

def test_inferred_model_validates_matching_row() -> None:
    """Inferred model accepts a row that matches the inferred types."""
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    Model = infer_model(data, model_name="User")
    inst = Model(id=3, name="Carol")
    assert inst.id == 3
    assert inst.name == "Carol"


def test_inferred_model_rejects_wrong_type() -> None:
    """Inferred model raises ValidationError when value has wrong type."""
    data = [{"count": 10}, {"count": 20}]
    Model = infer_model(data, model_name="Record")
    Model(count=5)
    with pytest.raises(ValidationError):
        Model(count="not_an_int")  # type: ignore[arg-type]


def test_inferred_model_accepts_none_when_nullable() -> None:
    """When column has None, model accepts None for that field."""
    data = [{"id": 1, "tag": "a"}, {"id": 2, "tag": None}]
    Model = infer_model(data, model_name="Record")
    Model(id=3, tag=None)
    Model(id=4, tag="b")


def test_inferred_model_optional_field_can_be_omitted() -> None:
    """When field is missing in some rows, model allows omitting it."""
    data = [{"id": 1, "name": "a"}, {"id": 2}]
    Model = infer_model(data, model_name="Record")
    Model(id=3)  # name omitted
    Model(id=4, name="b")


# ---- Config combinations ----

def test_config_both_string_options_false() -> None:
    """infer_string_numbers=False and infer_string_literals=False: all strings stay str."""
    data = [{"a": "42", "b": "true", "c": "null"}]
    config = InferConfig(infer_string_numbers=False, infer_string_literals=False)
    schema = infer_schema(data, config=config)
    assert schema["fields"]["a"]["type"] == "str"
    assert schema["fields"]["b"]["type"] == "str"
    assert schema["fields"]["c"]["type"] == "str"


def test_config_both_string_options_true() -> None:
    """infer_string_numbers=True and infer_string_literals=True: full CSV/JSON parsing."""
    data = [{"n": "42", "ok": "true", "empty": "null"}]
    config = InferConfig(infer_string_numbers=True, infer_string_literals=True)
    schema = infer_schema(data, config=config)
    assert schema["fields"]["n"]["type"] == "int"
    assert schema["fields"]["ok"]["type"] == "bool"
    assert schema["fields"]["empty"]["nullable"] is True


# ---- model_from_schema and schema shape ----

def test_model_from_schema_required_field_rejects_missing() -> None:
    """model_from_schema with required=True field raises when key is missing."""
    schema = {
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
        },
    }
    Model = model_from_schema(schema, model_name="M")
    Model(id=1)
    with pytest.raises(ValidationError):
        Model()  # type: ignore[call-arg]


def test_model_from_schema_optional_field_accepts_missing() -> None:
    """model_from_schema with required=False accepts missing key."""
    schema = {
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "name": {"type": "str", "required": False, "nullable": False},
        },
    }
    Model = model_from_schema(schema, model_name="M")
    Model(id=1)
    Model(id=2, name="x")


def test_model_from_schema_nullable_accepts_none() -> None:
    """model_from_schema with nullable=True accepts None."""
    schema = {
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "tag": {"type": "str", "required": True, "nullable": True},
        },
    }
    Model = model_from_schema(schema, model_name="M")
    Model(id=1, tag=None)
    Model(id=2, tag="a")


def test_model_from_schema_list_type() -> None:
    """model_from_schema with type list and item type builds list field."""
    schema = {
        "type": "model",
        "fields": {
            "ids": {"type": {"type": "list", "item": "int"}, "required": True, "nullable": False},
        },
    }
    Model = model_from_schema(schema, model_name="M")
    inst = Model(ids=[1, 2, 3])
    assert inst.ids == [1, 2, 3]


def test_model_from_schema_any_type() -> None:
    """model_from_schema with type any accepts any value."""
    schema = {
        "type": "model",
        "fields": {
            "x": {"type": "any", "required": True, "nullable": False},
        },
    }
    Model = model_from_schema(schema, model_name="M")
    Model(x=1)
    Model(x="hello")
    Model(x=[1, 2])


def test_get_fields_raises_on_invalid_schema() -> None:
    """get_fields raises ValueError when schema type is not 'model'."""
    with pytest.raises(ValueError, match="type.*model"):
        get_fields({"type": "list"})
    with pytest.raises(ValueError, match="type.*model"):
        get_fields({})


# ---- Invalid input (Rust raises) ----

def test_infer_schema_rejects_non_sequence() -> None:
    """infer_schema rejects non-iterable / non-sequence input."""
    with pytest.raises((ValueError, TypeError)):
        infer_schema("not a list")  # type: ignore[arg-type]
    with pytest.raises((ValueError, TypeError)):
        infer_schema(123)  # type: ignore[arg-type]


def test_infer_schema_rejects_list_of_non_mapping() -> None:
    """infer_schema rejects list of non-dict (e.g. list of lists)."""
    with pytest.raises((ValueError, TypeError)):
        infer_schema([[1, 2], [3, 4]])  # type: ignore[arg-type]


# ---- Numeric string edge cases ----

def test_string_zero_inferred_as_int() -> None:
    """'0' is inferred as int when number inference is on."""
    schema = infer_schema([{"n": "0"}, {"n": "0"}])
    assert schema["fields"]["n"]["type"] == "int"


def test_string_negative_inferred_as_int() -> None:
    """'-1' is inferred as int."""
    schema = infer_schema([{"n": "-1"}, {"n": "0"}])
    assert schema["fields"]["n"]["type"] == "int"


def test_string_whitespace_trimmed_for_number() -> None:
    """Whitespace around number is trimmed before parsing."""
    schema = infer_schema([{"n": "  42  "}, {"n": " 100 "}])
    assert schema["fields"]["n"]["type"] == "int"


def test_empty_string_stays_str() -> None:
    """Empty string is not inferred as number or null (stays str)."""
    schema = infer_schema([{"x": ""}, {"x": ""}])
    assert schema["fields"]["x"]["type"] == "str"


def test_int_and_float_strings_promote_to_float() -> None:
    """Mix of int-like and float-like strings promotes to float."""
    schema = infer_schema([{"x": "1"}, {"x": "2.5"}])
    assert schema["fields"]["x"]["type"] == "float"


# ---- Boolean and native types ----

def test_native_bool_inferred_as_bool() -> None:
    """Python True/False are inferred as bool."""
    schema = infer_schema([{"flag": True}, {"flag": False}])
    assert schema["fields"]["flag"]["type"] == "bool"


def test_native_int_float_inferred() -> None:
    """Native int and float are inferred correctly (no string parsing)."""
    schema = infer_schema([{"i": 1, "f": 1.5}])
    assert schema["fields"]["i"]["type"] == "int"
    assert schema["fields"]["f"]["type"] == "float"


# ---- Many rows and field count ----

def test_infer_schema_many_rows_same_shape() -> None:
    """Many rows with same shape: required True, types stable."""
    data = [{"id": i, "name": f"user_{i}"} for i in range(100)]
    schema = infer_schema(data)
    assert schema["fields"]["id"]["type"] == "int"
    assert schema["fields"]["name"]["type"] == "str"
    assert schema["fields"]["id"]["required"] is True
    assert schema["fields"]["name"]["required"] is True


def test_infer_schema_sparse_fields() -> None:
    """Many optional fields (each missing in at least one row)."""
    data = [
        {"a": 1, "b": 2},
        {"a": 3},
        {"b": 4},
    ]
    schema = infer_schema(data)
    assert schema["fields"]["a"]["required"] is False
    assert schema["fields"]["b"]["required"] is False
