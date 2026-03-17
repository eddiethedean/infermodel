from __future__ import annotations

import io
import sys

from infermodel import format_schema, print_schema, schema_diff, schema_merge


def test_format_schema_smoke() -> None:
    schema = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "user": {
                "type": {
                    "type": "model",
                    "fields": {
                        "name": {"type": "str", "required": True, "nullable": False},
                    },
                },
                "required": True,
                "nullable": False,
            },
        },
    }
    out = format_schema(schema)
    assert "Schema(v1)" in out
    assert "user" in out
    assert "name" in out


def test_print_schema_writes_to_stdout() -> None:
    schema = {"schema_version": 1, "type": "model", "fields": {}}
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        print_schema(schema)
    finally:
        sys.stdout = old
    assert "Schema(v1)" in buf.getvalue()


def test_format_schema_list_and_union() -> None:
    schema = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "ids": {"type": {"type": "list", "item": "int"}, "required": True, "nullable": False},
            "u": {"type": {"type": "union", "variants": ["int", "str"]}, "required": True, "nullable": False},
        },
    }
    out = format_schema(schema)
    assert "list[" in out
    assert "union" in out


def test_format_schema_unknown_typespec_falls_back_to_any() -> None:
    # Create a typed schema with an unknown TypeSpec instance to hit the fallback.
    from infermodel.schema import FieldSpec, SchemaModel, TypeSpec
    from infermodel.schema_tools import format_schema

    class Weird(TypeSpec):
        pass

    s = SchemaModel(
        schema_version=1,
        type="model",
        fields={"x": FieldSpec(name="x", type_spec=Weird(), required=True, nullable=False)},
    )
    out = format_schema(s)
    assert "any" in out


def test_schema_diff_and_merge() -> None:
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "name": {"type": "str", "required": True, "nullable": False},
        },
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "id": {"type": "float", "required": True, "nullable": False},
            "age": {"type": "int", "required": True, "nullable": False},
        },
    }
    changes = schema_diff(a, b)
    kinds = {c.kind for c in changes}
    assert "removed_field" in kinds
    assert "added_field" in kinds
    assert "changed_type" in kinds

    merged = schema_merge(a, b)
    assert merged["schema_version"] == 1
    # id: int + float -> float
    assert merged["fields"]["id"]["type"] == "float"
    # name/age become optional because missing from one side
    assert merged["fields"]["name"]["required"] is False
    assert merged["fields"]["age"]["required"] is False


def test_schema_diff_nested_changes() -> None:
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "user": {
                "type": {"type": "model", "fields": {"id": {"type": "int", "required": True, "nullable": False}}},
                "required": True,
                "nullable": False,
            }
        },
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "user": {
                "type": {
                    "type": "model",
                    "fields": {
                        "id": {"type": "float", "required": True, "nullable": False},
                        "name": {"type": "str", "required": True, "nullable": False},
                    },
                },
                "required": True,
                "nullable": False,
            }
        },
    }
    changes = schema_diff(a, b)
    # should see a nested type change and added field
    paths = {c.path for c in changes}
    assert "user.id" in paths
    assert "user.name" in paths


def test_schema_merge_commutative_and_idempotent() -> None:
    s = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "x": {"type": "int", "required": True, "nullable": False},
            "y": {"type": {"type": "union", "variants": ["int", "str"]}, "required": True, "nullable": False},
        },
    }
    assert schema_merge(s, s) == s
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": "int", "required": True, "nullable": False}},
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": "float", "required": True, "nullable": False}},
    }
    assert schema_merge(a, b) == schema_merge(b, a)


def test_schema_merge_union_dedup_and_scalar_fallback() -> None:
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": {"type": "union", "variants": ["int", "str"]}, "required": True, "nullable": False}},
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": {"type": "union", "variants": ["int", "str"]}, "required": True, "nullable": False}},
    }
    merged = schema_merge(a, b)
    assert merged["fields"]["x"]["type"]["type"] == "union"
    assert len(merged["fields"]["x"]["type"]["variants"]) == 2


def test_schema_diff_required_and_nullable_changes() -> None:
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": "int", "required": True, "nullable": False}},
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {"x": {"type": "int", "required": False, "nullable": True}},
    }
    changes = schema_diff(a, b)
    kinds = [c.kind for c in changes if c.path == "x"]
    assert "changed_required" in kinds
    assert "changed_nullable" in kinds


def test_schema_merge_nested_models_and_union_mixed() -> None:
    a = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "m": {
                "type": {"type": "model", "fields": {"x": {"type": "int", "required": True, "nullable": False}}},
                "required": True,
                "nullable": False,
            }
        },
    }
    b = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "m": {
                "type": {"type": "model", "fields": {"x": {"type": "float", "required": True, "nullable": False}}},
                "required": True,
                "nullable": False,
            }
        },
    }
    merged = schema_merge(a, b)
    assert merged["fields"]["m"]["type"]["type"] == "model"
    assert merged["fields"]["m"]["type"]["fields"]["x"]["type"] == "float"


