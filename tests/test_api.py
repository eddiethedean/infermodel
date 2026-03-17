"""Tests for public API: infer(...)."""

import pytest

from infermodel import InferConfig, infer, model_from_schema
from infermodel import infer_iter, infer_iter_rows


def test_infer_schema_flat():
    data = [
        {"id": 1, "name": "a"},
        {"id": 2, "name": "b"},
    ]
    res = infer(data, return_model=False)
    schema = res.schema_dict
    assert schema is not None
    assert schema["schema_version"] == 1
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
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["name"]["required"] is False


def test_infer_schema_nullable():
    data = [
        {"id": 1, "name": "a"},
        {"id": 2, "name": None},
    ]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["name"]["nullable"] is True


def test_infer_schema_int_float_promotion():
    data = [
        {"x": 1},
        {"x": 1.5},
    ]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["x"]["type"] == "float"


def test_infer_model_flat():
    data = [{"id": 1, "name": "Alice"}]
    Model = infer(data, model_name="Record").model
    assert Model is not None
    assert "id" in Model.model_fields
    assert "name" in Model.model_fields
    rec = Model(id=1, name="Alice")
    assert rec.id == 1
    assert rec.name == "Alice"


def test_infer_schema_nested_single_level():
    data = [
        {"id": 1, "user": {"name": "Alice", "age": 30}},
        {"id": 2, "user": {"name": "Bob", "age": 25}},
    ]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["type"] == "model"
    assert "user" in schema["fields"]
    user_field = schema["fields"]["user"]
    assert isinstance(user_field["type"], dict)
    assert user_field["type"]["type"] == "model"
    assert set(user_field["type"]["fields"].keys()) == {"name", "age"}


def test_infer_model_nested_single_level():
    data = [
        {"id": 1, "user": {"name": "Alice", "age": 30}},
        {"id": 2, "user": {"name": "Bob", "age": 25}},
    ]
    Model = infer(data, model_name="Record").model
    assert Model is not None
    assert "user" in Model.model_fields
    inst = Model(id=3, user={"name": "Carol", "age": 22})
    assert inst.user.name == "Carol"
    assert inst.user.age == 22


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


def test_model_from_schema_exported_from_package():
    # Import from top-level package to ensure it is part of the public API.
    from infermodel import model_from_schema as exported  # type: ignore[redefined-builtin]

    schema = {
        "type": "model",
        "fields": {
            "x": {"type": "int", "required": True, "nullable": False},
        },
    }
    Model = exported(schema, model_name="Exported")
    assert Model(x=1).x == 1


def test_infer_schema_with_config():
    data = [{"a": 1}]
    config = InferConfig()
    schema = infer(data, config=config, return_model=False).schema_dict
    assert schema is not None
    assert schema["type"] == "model"
    assert schema["fields"]["a"]["type"] == "int"


def test_infer_schema_accepts_tuple():
    """Iterable includes tuple, not just list."""
    data = ({"id": 1}, {"id": 2})
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["type"] == "model"
    assert schema["fields"]["id"]["type"] == "int"


def test_infer_schema_accepts_generator():
    """Iterable includes generator; inference uses first sample_size items."""
    def rows():
        yield {"id": 1, "x": "a"}
        yield {"id": 2, "x": "b"}
    schema = infer(rows(), return_model=False).schema_dict
    assert schema is not None
    assert schema["type"] == "model"
    assert schema["fields"]["id"]["type"] == "int"
    assert schema["fields"]["x"]["type"] == "str"


def test_infer_schema_sample_size_caps_rows():
    """sample_size limits how many rows are used for inference."""
    # 5 rows; with sample_size=2 only first 2 are used (both have "a")
    data = ({"a": i} for i in range(5))
    config = InferConfig(sample_size=2)
    schema = infer(data, config=config, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["a"]["type"] == "int"
    # With sample_size=1 we still get one row
    data2 = ({"b": 1} for _ in range(10))
    schema2 = infer(data2, config=InferConfig(sample_size=1), return_model=False).schema_dict
    assert schema2 is not None
    assert schema2["fields"]["b"]["type"] == "int"


def test_infer_schema_default_number_strings_inferred():
    """Default: number strings are inferred as int/float."""
    data = [{"count": "42"}, {"count": "100"}]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["count"]["type"] == "int"
    data_float = [{"x": "3.14"}, {"x": "2.5"}]
    schema2 = infer(data_float, return_model=False).schema_dict
    assert schema2 is not None
    assert schema2["fields"]["x"]["type"] == "float"


def test_infer_schema_no_number_inference_when_disabled():
    """With infer_string_numbers=False, string columns stay str."""
    data = [{"count": "42"}, {"name": "hello"}]
    schema = infer(
        data, config=InferConfig(infer_string_numbers=False), return_model=False
    ).schema_dict
    assert schema is not None
    assert schema["fields"]["count"]["type"] == "str"
    assert schema["fields"]["name"]["type"] == "str"


def test_infer_schema_string_looks_like_int():
    """String columns that look like integers are inferred as int (default)."""
    data = [{"count": "42"}, {"count": "100"}]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["count"]["type"] == "int"


def test_infer_schema_string_looks_like_float():
    """String columns that look like floats are inferred as float (default)."""
    data = [{"x": "3.14"}, {"x": "2.5"}]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["x"]["type"] == "float"


def test_infer_schema_string_mixed_numeric_and_text():
    """String column with mix of numeric and non-numeric merges to any."""
    data = [{"id": "42"}, {"id": "hello"}]
    schema = infer(data, return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["id"]["type"] == "any"


def test_infer_schema_string_looks_like_bool():
    """With infer_string_literals=True, string columns that look like booleans are inferred as bool."""
    data = [{"active": "true"}, {"active": "false"}]
    schema = infer(
        data, config=InferConfig(infer_string_literals=True), return_model=False
    ).schema_dict
    assert schema is not None
    assert schema["fields"]["active"]["type"] == "bool"

    data_yes_no = [{"flag": "yes"}, {"flag": "no"}]
    schema2 = infer(
        data_yes_no, config=InferConfig(infer_string_literals=True), return_model=False
    ).schema_dict
    assert schema2 is not None
    assert schema2["fields"]["flag"]["type"] == "bool"


def test_infer_schema_string_null_like_nullable():
    """With infer_string_literals=True, string 'null' is treated as null (column becomes nullable)."""
    data = [{"id": "1"}, {"id": "null"}]
    schema = infer(
        data, config=InferConfig(infer_string_literals=True), return_model=False
    ).schema_dict
    assert schema is not None
    assert schema["fields"]["id"]["nullable"] is True
    assert schema["fields"]["id"]["type"] == "int"


def test_infer_schema_json_style_strings():
    """With infer_string_literals=True, null/bool from strings; numbers inferred by default."""
    data = [
        {"count": "42", "active": "true", "note": "ok"},
        {"count": "0", "active": "false", "note": "null"},
    ]
    schema = infer(
        data, config=InferConfig(infer_string_literals=True), return_model=False
    ).schema_dict
    assert schema is not None
    assert schema["fields"]["count"]["type"] == "int"
    assert schema["fields"]["active"]["type"] == "bool"
    assert schema["fields"]["note"]["nullable"] is True


def test_config_preset_for_csv() -> None:
    data = [{"active": "true"}, {"active": "false"}]
    schema = infer(data, config=InferConfig.for_csv(), return_model=False).schema_dict
    assert schema is not None
    assert schema["fields"]["active"]["type"] == "bool"


def test_config_presets_strict_and_permissive_smoke() -> None:
    # permissive should not raise on dict/non-dict conflicts
    data = [{"x": {"a": 1}}, {"x": 1}]
    res = infer(data, config=InferConfig.permissive(), return_model=False)
    assert res.schema_dict is not None

    # strict should raise on dict/non-dict conflicts
    with pytest.raises(ValueError):
        infer(data, config=InferConfig.strict(), return_model=False)


def test_infer_iter_yields_instances_for_generator() -> None:
    def rows():
        yield {"id": 1, "name": "a"}
        yield {"id": 2, "name": "b"}

    res, it = infer_iter(rows(), model_name="Row")
    assert res.model is not None
    items = list(it)
    assert len(items) == 2
    assert items[0].id == 1
    assert items[1].name == "b"


def test_infer_iter_rows_yields_row_and_error() -> None:
    data = [
        {"id": 1},
        {"id": "oops"},  # invalid once inferred as int
        {"id": 2},
    ]
    # Force inference from first row only so later string row is invalid.
    res, it = infer_iter_rows(data, model_name="Row", config=InferConfig(sample_size=1))
    assert res.model is not None
    out = list(it)
    assert out[0][1] is not None and out[0][2] is None
    assert out[1][1] is None and out[1][2] is not None
    assert out[2][1] is not None and out[2][2] is None


def test_infer_diagnostics_truncation_flag() -> None:
    # sample_size=1 and 3 rows should report maybe_truncated=True with rows_used=1
    data = [{"x": 1}, {"x": 2}, {"x": 3}]
    res = infer(data, return_model=False, return_diagnostics=True, config=InferConfig(sample_size=1))
    assert res.diagnostics is not None
    assert res.diagnostics["rows_used"] == 1
    assert res.diagnostics["maybe_truncated"] is True

    # sample_size=0 (no limit) should not truncate
    res2 = infer(data, return_model=False, return_diagnostics=True, config=InferConfig(sample_size=0))
    assert res2.diagnostics is not None
    assert res2.diagnostics["rows_used"] == 3
    assert res2.diagnostics["maybe_truncated"] is False


def test_infer_iter_sample_size_zero_buffers_all_before_yield() -> None:
    consumed = []

    def rows():
        for i in range(3):
            consumed.append(i)
            yield {"x": i}

    res, it = infer_iter(rows(), config=InferConfig(sample_size=0), model_name="R")
    # if sample_size=0, inference consumes entire iterable up-front
    assert consumed == [0, 1, 2]
    items = list(it)
    assert [m.x for m in items] == [0, 1, 2]


def test_infer_iter_rows_sample_size_zero_yields_errors_without_stopping() -> None:
    data = [{"x": 1}, {"x": "bad"}, {"x": 2}]
    res, it = infer_iter_rows(data, config=InferConfig(sample_size=0), model_name="R")
    out = list(it)
    assert out[0][1] is not None and out[0][2] is None
    # schema inferred from all rows -> likely any; force strict by sample_size=1 to ensure error
    res2, it2 = infer_iter_rows(data, config=InferConfig(sample_size=1), model_name="R")
    out2 = list(it2)
    assert out2[1][1] is None and out2[1][2] is not None


def test_infer_iter_empty_iterable_does_not_crash() -> None:
    def rows():
        if False:
            yield {"x": 1}

    res, it = infer_iter(rows(), config=InferConfig(sample_size=10), model_name="R")
    assert res.schema_dict is not None
    assert list(it) == []


def test_infer_iter_rows_empty_iterable() -> None:
    def rows():
        if False:
            yield {"x": 1}

    res, it = infer_iter_rows(rows(), config=InferConfig(sample_size=5), model_name="R")
    assert res.schema_dict is not None
    assert list(it) == []


def test_infer_iter_consumes_buffer_then_remainder() -> None:
    def rows():
        for i in range(5):
            yield {"x": i}

    res, it = infer_iter(rows(), config=InferConfig(sample_size=2), model_name="R")
    items = list(it)
    assert [m.x for m in items] == [0, 1, 2, 3, 4]
