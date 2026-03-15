"""Tests for public API: infer_schema and infer_model."""

from infermodel import infer_schema, infer_model, InferConfig
from infermodel.emit_pydantic import model_from_schema


def test_infer_schema_flat():
    data = [
        {"id": 1, "name": "a"},
        {"id": 2, "name": "b"},
    ]
    schema = infer_schema(data)
    assert schema["type"] == "model"
    assert "fields" in schema
    assert "id" in schema["fields"]
    assert "name" in schema["fields"]
    assert schema["fields"]["id"]["type"] == "int"
    assert schema["fields"]["name"]["type"] == "str"
    assert schema["fields"]["id"]["required"] is True
    assert schema["fields"]["id"]["nullable"] is False


def test_infer_schema_optional_field():
    data = [
        {"id": 1, "name": "a"},
        {"id": 2},
    ]
    schema = infer_schema(data)
    assert schema["fields"]["name"]["required"] is False


def test_infer_schema_nullable():
    data = [
        {"id": 1, "name": "a"},
        {"id": 2, "name": None},
    ]
    schema = infer_schema(data)
    assert schema["fields"]["name"]["nullable"] is True


def test_infer_schema_int_float_promotion():
    data = [
        {"x": 1},
        {"x": 1.5},
    ]
    schema = infer_schema(data)
    assert schema["fields"]["x"]["type"] == "float"


def test_infer_model_flat():
    data = [{"id": 1, "name": "Alice"}]
    Model = infer_model(data, model_name="Record")
    assert "id" in Model.model_fields
    assert "name" in Model.model_fields
    rec = Model(id=1, name="Alice")
    assert rec.id == 1
    assert rec.name == "Alice"


def test_model_from_schema():
    schema = {
        "type": "model",
        "fields": {
            "id": {"type": "int", "required": True, "nullable": False},
            "name": {"type": "str", "required": False, "nullable": True},
        },
    }
    Model = model_from_schema(schema, model_name="User")
    assert "id" in Model.model_fields
    assert "name" in Model.model_fields
    inst = Model(id=1, name=None)
    assert inst.id == 1
    assert inst.name is None


def test_infer_schema_with_config():
    data = [{"a": 1}]
    config = InferConfig()
    schema = infer_schema(data, config=config)
    assert schema["type"] == "model"
    assert schema["fields"]["a"]["type"] == "int"


def test_infer_schema_accepts_tuple():
    """Sequence includes tuple, not just list."""
    data = ({"id": 1}, {"id": 2})
    schema = infer_schema(data)
    assert schema["type"] == "model"
    assert schema["fields"]["id"]["type"] == "int"
