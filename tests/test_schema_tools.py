from __future__ import annotations

from infermodel import format_schema, schema_diff, schema_merge


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

