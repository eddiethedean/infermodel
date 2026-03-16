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
    with pytest.raises(TypeError):
        infer_schema("not a list")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        infer_schema(123)  # type: ignore[arg-type]


def test_infer_schema_rejects_list_of_non_mapping() -> None:
    """infer_schema rejects list of non-dict (e.g. list of lists)."""
    with pytest.raises(TypeError):
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


def test_infer_schema_sample_size_zero_means_no_limit() -> None:
    """sample_size=0 means no limit; inference should consume the full iterable."""
    def rows():
        yield {"x": 1}
        yield {"x": 2}
        yield {"x": 3}
    schema = infer_schema(rows(), config=InferConfig(sample_size=0))
    assert schema["fields"]["x"]["type"] == "int"


def test_infer_schema_large_sample_size_is_ok() -> None:
    """Very large sample_size behaves like 'no cap' for small inputs (no overflow/weirdness)."""
    schema = infer_schema([{"x": 1}, {"x": 2}], config=InferConfig(sample_size=10_000_000))
    assert schema["fields"]["x"]["type"] == "int"


def test_numeric_promotion_strict_yields_any_on_int_float_mix() -> None:
    """With numeric_promotion='strict', int+float does not promote to float (falls back to any)."""
    data = [{"x": 1}, {"x": 1.5}]
    schema = infer_schema(data, config=InferConfig(numeric_promotion="strict"))
    assert schema["fields"]["x"]["type"] == "any"


def test_infer_schema_optional_nested_dict() -> None:
    """Nested dict field present in some rows only -> optional nested field."""
    data = [
        {"id": 1, "meta": {"flag": True}},
        {"id": 2},
    ]
    schema = infer_schema(data)
    meta = schema["fields"]["meta"]
    assert meta["required"] is False
    assert isinstance(meta["type"], dict)
    assert meta["type"]["type"] == "model"
    assert set(meta["type"]["fields"].keys()) == {"flag"}


def test_infer_schema_nullable_nested_dict() -> None:
    """Nested dict field that is sometimes None -> nullable nested field."""
    data = [
        {"id": 1, "meta": {"flag": True}},
        {"id": 2, "meta": None},
    ]
    schema = infer_schema(data)
    meta = schema["fields"]["meta"]
    assert meta["nullable"] is True


def test_inferred_nested_model_validates() -> None:
    """Inferred nested model enforces types in nested structure."""
    data = [
        {"id": 1, "user": {"name": "Alice", "age": 30}},
        {"id": 2, "user": {"name": "Bob", "age": 25}},
    ]
    Model = infer_model(data, model_name="UserWithNested")
    Model(id=3, user={"name": "Carol", "age": 22})
    with pytest.raises(ValidationError):
        Model(id=4, user={"name": "Dave", "age": "not_an_int"})  # type: ignore[arg-type]


def test_infer_schema_multi_level_nested_dict() -> None:
    """Multi-level nested dicts produce nested model schemas recursively."""
    data = [
        {"user": {"profile": {"age": 30, "active": True}}},
        {"user": {"profile": {"age": 25, "active": False}}},
    ]
    schema = infer_schema(data)
    user_type = schema["fields"]["user"]["type"]
    assert isinstance(user_type, dict)
    assert user_type["type"] == "model"
    profile_type = user_type["fields"]["profile"]["type"]
    assert isinstance(profile_type, dict)
    assert profile_type["type"] == "model"
    assert profile_type["fields"]["age"]["type"] == "int"
    assert profile_type["fields"]["active"]["type"] == "bool"


def test_infer_model_multi_level_nested_dict_validates() -> None:
    """Multi-level nested inferred models validate deeply nested values."""
    data = [
        {"user": {"profile": {"age": 30, "active": True}}},
        {"user": {"profile": {"age": 25, "active": False}}},
    ]
    Model = infer_model(data, model_name="Deep")
    ok = Model(user={"profile": {"age": 40, "active": True}})
    assert ok.user.profile.age == 40
    with pytest.raises(ValidationError):
        Model(user={"profile": {"age": "nope", "active": True}})  # type: ignore[arg-type]


def test_nested_required_vs_nullable_semantics() -> None:
    """Nested fields track required vs nullable independently inside the nested model."""
    data = [
        {"user": {"name": "Alice", "nickname": None}},
        {"user": {"name": "Bob"}},
    ]
    schema = infer_schema(data)
    user_fields = schema["fields"]["user"]["type"]["fields"]
    assert user_fields["name"]["required"] is True
    assert user_fields["name"]["nullable"] is False
    # Nested required semantics match top-level: missing in any observed nested dict => required=False.
    assert user_fields["nickname"]["required"] is False
    assert user_fields["nickname"]["nullable"] is True   # explicitly None in one row

    Model = infer_model(data, model_name="NestedSemantics")
    Model(user={"name": "Carol"})  # nickname omitted
    Model(user={"name": "Dave", "nickname": None})


def test_dict_and_scalar_conflict_merges_to_any() -> None:
    """When a field is observed as both dict and non-dict, default policy merges to any."""
    data = [
        {"meta": {"flag": True}},
        {"meta": 1},
    ]
    schema = infer_schema(data)
    assert schema["fields"]["meta"]["type"] == "any"


def test_model_from_schema_nested_model_field() -> None:
    """model_from_schema builds nested Pydantic models for model-typed fields."""
    schema = {
        "type": "model",
        "fields": {
            "user": {
                "type": {
                    "type": "model",
                    "fields": {
                        "id": {"type": "int", "required": True, "nullable": False},
                        "name": {"type": "str", "required": True, "nullable": False},
                    },
                },
                "required": True,
                "nullable": False,
            }
        },
    }
    Model = model_from_schema(schema, model_name="FromSchemaNested")
    inst = Model(user={"id": 1, "name": "Alice"})
    assert inst.user.id == 1
    with pytest.raises(ValidationError):
        Model(user={"id": "nope", "name": "Bob"})  # type: ignore[arg-type]


def test_dict_mixed_policy_union_produces_union_type() -> None:
    """With dict_mixed_policy='union', dict+non-dict conflicts produce a union type."""
    data = [
        {"meta": {"flag": True}},
        {"meta": 1},
    ]
    schema = infer_schema(data, config=InferConfig(dict_mixed_policy="union"))
    meta_type = schema["fields"]["meta"]["type"]
    assert isinstance(meta_type, dict)
    assert meta_type["type"] == "union"
    assert len(meta_type["variants"]) == 2


def test_dict_mixed_policy_error_raises_value_error() -> None:
    """With dict_mixed_policy='error', dict+non-dict conflicts raise ValueError."""
    data = [
        {"meta": {"flag": True}},
        {"meta": 1},
    ]
    with pytest.raises(ValueError):
        infer_schema(data, config=InferConfig(dict_mixed_policy="error"))


def test_invalid_policy_value_raises_type_error() -> None:
    """Invalid policy strings are rejected with TypeError (invalid input)."""
    data = [{"x": 1}]
    with pytest.raises(TypeError):
        infer_schema(data, config=InferConfig(dict_mixed_policy="bogus"))  # type: ignore[arg-type]
