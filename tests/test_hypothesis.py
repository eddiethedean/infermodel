"""Hypothesis property-based tests for infer_schema and infer_model."""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given, settings

from infermodel import infer_schema, infer_model, InferConfig
from infermodel.emit_pydantic import model_from_schema


# Keys must be strings (required by inference).
field_names = st.text(min_size=1, max_size=32, alphabet="abcdefghijklmnopqrstuvwxyz_").filter(
    lambda s: s.isidentifier() or s.replace("_", "").isalnum()
)

# Primitive values that inference supports (flat).
primitive_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=100),
)

# A single row: dict of str -> primitive.
row = st.dictionaries(keys=field_names, values=primitive_values, min_size=0, max_size=15)

# Data: list of rows (sequence of mappings).
list_of_dicts = st.lists(row, min_size=0, max_size=50)


@given(data=list_of_dicts)
@settings(max_examples=200, deadline=2000)
def test_infer_schema_never_crashes(data: list[dict]) -> None:
    """infer_schema accepts any list of dicts with string keys and primitive values."""
    schema = infer_schema(data)
    assert isinstance(schema, dict)
    assert schema.get("type") == "model"
    assert "fields" in schema
    assert isinstance(schema["fields"], dict)
    scalar_types = ("any", "bool", "int", "float", "str", "date", "datetime", "time")
    for name, field in schema["fields"].items():
        assert isinstance(name, str)
        assert "type" in field
        assert "required" in field
        assert "nullable" in field
        t = field["type"]
        assert isinstance(t, (str, dict))
        if isinstance(t, str):
            assert t in scalar_types


@given(data=list_of_dicts)
@settings(max_examples=200, deadline=2000)
def test_infer_schema_then_model_from_schema_no_crash(data: list[dict]) -> None:
    """model_from_schema(infer_schema(data)) builds a model without raising."""
    schema = infer_schema(data)
    model = model_from_schema(schema, model_name="Inferred")
    assert model is not None


# Rows with only str or None, and fixed key set (round-trip when infer_string_numbers=False).
str_or_none = st.one_of(st.none(), st.text(max_size=80))


@st.composite
def list_of_str_dicts_same_keys(draw: st.DrawFn) -> list[dict]:
    """Generate list of dicts with the same keys and str/None values (so every row validates)."""
    keys = draw(st.lists(field_names, min_size=1, max_size=10, unique=True))
    row_strategy = st.fixed_dictionaries(
        {k: str_or_none for k in keys},
    )
    return draw(st.lists(row_strategy, min_size=1, max_size=25))


@given(data=list_of_str_dicts_same_keys())
@settings(max_examples=150, deadline=2000)
def test_round_trip_when_strings_only_and_no_number_inference(data: list[dict]) -> None:
    """With infer_string_numbers=False and only str/None, each row validates against the inferred model."""
    config = InferConfig(infer_string_numbers=False)
    model = infer_model(data, model_name="Record", config=config)
    for row in data:
        model(**row)
