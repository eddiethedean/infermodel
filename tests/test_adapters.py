from __future__ import annotations

import json

import pytest

from infermodel import InferConfig
from infermodel.adapters import infer_from_csv, infer_from_json, infer_from_ndjson


def test_infer_from_csv(tmp_path) -> None:
    p = tmp_path / "data.csv"
    p.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
    res = infer_from_csv(p, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"
    assert res.schema_dict["fields"]["name"]["type"] == "str"


def test_infer_from_json(tmp_path) -> None:
    p = tmp_path / "data.json"
    p.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    res = infer_from_json(p, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"


def test_infer_from_ndjson(tmp_path) -> None:
    p = tmp_path / "data.ndjson"
    p.write_text('{"id": "1"}\n{"id": "2"}\n', encoding="utf-8")
    res = infer_from_ndjson(
        p,
        config=InferConfig(infer_string_numbers=True),
        return_model=False,
    )
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"


def test_infer_from_dataframe_requires_pandas() -> None:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        pytest.skip("pandas not installed")

    from infermodel.adapters import infer_from_dataframe

    df = pd.DataFrame([{"a": 1}, {"a": 2}])
    res = infer_from_dataframe(df, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"


def test_infer_from_parquet_requires_pyarrow(tmp_path) -> None:
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        pytest.skip("pyarrow not installed")

    from infermodel.adapters import infer_from_parquet

    table = pa.table({"a": [1, 2, 3]})
    p = tmp_path / "data.parquet"
    pq.write_table(table, p)

    res = infer_from_parquet(p, return_model=False, batch_size=2)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"

