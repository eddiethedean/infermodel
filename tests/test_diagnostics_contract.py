from __future__ import annotations

from typing import Any, Mapping

from infermodel import InferConfig, infer


def _assert_field_diag_shape(d: Mapping[str, Any]) -> None:
    assert "presence_count" in d
    assert "missing_count" in d
    assert "null_count" in d
    assert "type_counts" in d
    assert isinstance(d["presence_count"], int)
    assert isinstance(d["missing_count"], int)
    assert isinstance(d["null_count"], int)
    assert isinstance(d["type_counts"], dict)


def test_diagnostics_contract_top_level_keys() -> None:
    res = infer([{"a": 1}, {"a": 2}], return_model=False, return_diagnostics=True)
    diag = res.diagnostics
    assert isinstance(diag, dict)
    assert set(diag.keys()) >= {"rows_used", "sample_size", "maybe_truncated", "fields"}
    assert isinstance(diag["rows_used"], int)
    assert isinstance(diag["sample_size"], int)
    assert isinstance(diag["maybe_truncated"], bool)
    assert isinstance(diag["fields"], dict)


def test_diagnostics_field_counts_and_missing_math() -> None:
    data = [
        {"a": 1, "b": None},
        {"a": 2},
        {"a": 3, "b": 5},
    ]
    res = infer(
        data,
        return_model=False,
        return_diagnostics=True,
        config=InferConfig(sample_size=2),
    )
    diag = res.diagnostics
    assert diag is not None

    assert diag["rows_used"] == 2
    assert diag["sample_size"] == 2
    assert diag["maybe_truncated"] is True

    fields = diag["fields"]
    assert isinstance(fields, dict)
    assert set(fields.keys()) >= {"a", "b"}

    a = fields["a"]
    b = fields["b"]
    _assert_field_diag_shape(a)
    _assert_field_diag_shape(b)

    # "a" present in both sampled rows
    assert a["presence_count"] == 2
    assert a["missing_count"] == 0

    # "b" present in only the first sampled row, where it is explicitly None
    assert b["presence_count"] == 1
    assert b["missing_count"] == 1
    assert b["null_count"] == 1


def test_diagnostics_type_counts_has_expected_buckets() -> None:
    data = [
        {"x": 1},
        {"x": "s"},
        {"x": None},
        {"x": {"k": 1}},
    ]
    res = infer(
        data,
        return_model=False,
        return_diagnostics=True,
        config=InferConfig(sample_size=0),
    )
    diag = res.diagnostics
    assert diag is not None
    fields = diag["fields"]
    assert isinstance(fields, dict)
    x = fields["x"]
    _assert_field_diag_shape(x)

    counts = x["type_counts"]
    assert isinstance(counts, dict)
    # The exact bucket names are classifier-defined; we assert presence of likely ones.
    assert any(k.lower().startswith("int") for k in counts.keys())
    assert any(k.lower().startswith("str") for k in counts.keys())
    assert any(k.lower().startswith("none") for k in counts.keys())
    assert any(k.lower().startswith("dict") for k in counts.keys())

