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
    """Iterable includes tuple, not just list."""
    data = ({"id": 1}, {"id": 2})
    schema = infer_schema(data)
    assert schema["type"] == "model"
    assert schema["fields"]["id"]["type"] == "int"


def test_infer_schema_accepts_generator():
    """Iterable includes generator; inference uses first sample_size items."""
    def rows():
        yield {"id": 1, "x": "a"}
        yield {"id": 2, "x": "b"}
    schema = infer_schema(rows())
    assert schema["type"] == "model"
    assert schema["fields"]["id"]["type"] == "int"
    assert schema["fields"]["x"]["type"] == "str"


def test_infer_schema_sample_size_caps_rows():
    """sample_size limits how many rows are used for inference."""
    # 5 rows; with sample_size=2 only first 2 are used (both have "a")
    data = ({"a": i} for i in range(5))
    config = InferConfig(sample_size=2)
    schema = infer_schema(data, config=config)
    assert schema["fields"]["a"]["type"] == "int"
    # With sample_size=1 we still get one row
    data2 = ({"b": 1} for _ in range(10))
    schema2 = infer_schema(data2, config=InferConfig(sample_size=1))
    assert schema2["fields"]["b"]["type"] == "int"


def test_infer_schema_default_number_strings_inferred():
    """Default: number strings are inferred as int/float."""
    data = [{"count": "42"}, {"count": "100"}]
    schema = infer_schema(data)
    assert schema["fields"]["count"]["type"] == "int"
    data_float = [{"x": "3.14"}, {"x": "2.5"}]
    schema2 = infer_schema(data_float)
    assert schema2["fields"]["x"]["type"] == "float"


def test_infer_schema_no_number_inference_when_disabled():
    """With infer_string_numbers=False, string columns stay str."""
    data = [{"count": "42"}, {"name": "hello"}]
    schema = infer_schema(data, config=InferConfig(infer_string_numbers=False))
    assert schema["fields"]["count"]["type"] == "str"
    assert schema["fields"]["name"]["type"] == "str"


def test_infer_schema_string_looks_like_int():
    """String columns that look like integers are inferred as int (default)."""
    data = [{"count": "42"}, {"count": "100"}]
    schema = infer_schema(data)
    assert schema["fields"]["count"]["type"] == "int"


def test_infer_schema_string_looks_like_float():
    """String columns that look like floats are inferred as float (default)."""
    data = [{"x": "3.14"}, {"x": "2.5"}]
    schema = infer_schema(data)
    assert schema["fields"]["x"]["type"] == "float"


def test_infer_schema_string_mixed_numeric_and_text():
    """String column with mix of numeric and non-numeric merges to any."""
    data = [{"id": "42"}, {"id": "hello"}]
    schema = infer_schema(data)
    assert schema["fields"]["id"]["type"] == "any"


def test_infer_schema_string_looks_like_bool():
    """With infer_string_literals=True, string columns that look like booleans are inferred as bool."""
    data = [{"active": "true"}, {"active": "false"}]
    schema = infer_schema(data, config=InferConfig(infer_string_literals=True))
    assert schema["fields"]["active"]["type"] == "bool"

    data_yes_no = [{"flag": "yes"}, {"flag": "no"}]
    schema2 = infer_schema(data_yes_no, config=InferConfig(infer_string_literals=True))
    assert schema2["fields"]["flag"]["type"] == "bool"


def test_infer_schema_string_null_like_nullable():
    """With infer_string_literals=True, string 'null' is treated as null (column becomes nullable)."""
    data = [{"id": "1"}, {"id": "null"}]
    schema = infer_schema(data, config=InferConfig(infer_string_literals=True))
    assert schema["fields"]["id"]["nullable"] is True
    assert schema["fields"]["id"]["type"] == "int"


def test_infer_schema_json_style_strings():
    """With infer_string_literals=True, null/bool from strings; numbers inferred by default."""
    data = [
        {"count": "42", "active": "true", "note": "ok"},
        {"count": "0", "active": "false", "note": "null"},
    ]
    schema = infer_schema(data, config=InferConfig(infer_string_literals=True))
    assert schema["fields"]["count"]["type"] == "int"
    assert schema["fields"]["active"]["type"] == "bool"
    assert schema["fields"]["note"]["nullable"] is True
