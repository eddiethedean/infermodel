from __future__ import annotations

import pytest

from infermodel.schema import (
    ModelTypeSpec,
    TypeSpec,
    schema_from_dict,
    type_spec_from_obj,
    type_spec_to_obj,
)


def test_schema_from_dict_rejects_bad_version() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        schema_from_dict({"schema_version": 2, "type": "model", "fields": {}})


def test_schema_from_dict_rejects_non_model_type() -> None:
    with pytest.raises(ValueError, match="type"):
        schema_from_dict({"schema_version": 1, "type": "list", "fields": {}})


def test_schema_from_dict_rejects_bad_fields_container() -> None:
    with pytest.raises(TypeError, match="fields.*mapping"):
        schema_from_dict({"schema_version": 1, "type": "model", "fields": []})


def test_schema_from_dict_fields_none_is_treated_as_empty() -> None:
    s = schema_from_dict({"schema_version": 1, "type": "model", "fields": None})
    assert s.to_dict()["fields"] == {}


def test_schema_from_dict_rejects_non_string_field_names() -> None:
    with pytest.raises(TypeError, match="field names"):
        schema_from_dict({"schema_version": 1, "type": "model", "fields": {1: {"type": "int"}}})


def test_schema_from_dict_rejects_bad_field_spec_shape() -> None:
    with pytest.raises(TypeError, match="Field spec"):
        schema_from_dict({"schema_version": 1, "type": "model", "fields": {"x": 123}})


def test_type_spec_from_obj_unknown_scalar_becomes_any() -> None:
    ts = type_spec_from_obj("bogus")
    assert getattr(ts, "tag", None) == "any"


def test_type_spec_from_obj_union_variants_must_be_sequence() -> None:
    with pytest.raises(TypeError, match="union variants"):
        type_spec_from_obj({"type": "union", "variants": {"a": 1}})


def test_type_spec_from_obj_model_fields_must_be_mapping() -> None:
    with pytest.raises(TypeError, match="model fields"):
        type_spec_from_obj({"type": "model", "fields": []})


def test_type_spec_from_obj_model_nested_field_names_must_be_strings() -> None:
    with pytest.raises(TypeError, match="Nested field names"):
        type_spec_from_obj({"type": "model", "fields": {1: {"type": "int"}}})


def test_type_spec_from_obj_model_nested_field_specs_must_be_mappings() -> None:
    with pytest.raises(TypeError, match="Nested field spec"):
        type_spec_from_obj({"type": "model", "fields": {"x": 1}})


def test_schema_round_trip_stable() -> None:
    raw = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "tags": {"type": {"type": "list", "item": "str"}, "required": False, "nullable": False},
            "u": {
                "type": {"type": "union", "variants": ["int", "float"]},
                "required": True,
                "nullable": True,
            },
            "nested": {
                "type": {"type": "model", "fields": {"x": {"type": "str", "required": True, "nullable": False}}},
                "required": True,
                "nullable": False,
            },
        },
    }
    s = schema_from_dict(raw)
    assert s.to_dict() == raw


def test_type_spec_to_obj_unknown_falls_back_to_any() -> None:
    class Weird(TypeSpec):
        pass

    assert type_spec_to_obj(Weird()) == "any"


def test_type_spec_to_obj_model_emits_fields() -> None:
    spec = ModelTypeSpec(fields={})
    obj = type_spec_to_obj(spec)
    assert obj["type"] == "model"
    assert obj["fields"] == {}

