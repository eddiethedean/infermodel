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


def test_infer_from_sqlalchemy_smoke() -> None:
    try:
        from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select
    except Exception:
        pytest.skip("sqlalchemy not installed")

    from infermodel.adapters import infer_from_sqlalchemy

    engine = create_engine("sqlite+pysqlite:///:memory:")
    md = MetaData()
    users = Table(
        "users",
        md,
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    md.create_all(engine)
    with engine.begin() as conn:
        conn.execute(users.insert(), [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])

    res = infer_from_sqlalchemy(engine, select(users), return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"
    assert res.schema_dict["fields"]["name"]["type"] == "str"


def test_infer_from_mongodb_requires_pymongo() -> None:
    try:
        import pymongo  # noqa: F401
    except Exception:
        pytest.skip("pymongo not installed")

    from infermodel.adapters import infer_from_mongodb

    class FakeCollection:
        def find(self, *args, **kwargs):
            return iter([{"a": 1}, {"a": 2}])

    res = infer_from_mongodb(FakeCollection(), return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"


def test_infer_from_dynamodb_requires_boto3() -> None:
    try:
        import boto3  # noqa: F401
    except Exception:
        pytest.skip("boto3 not installed")

    from infermodel.adapters import infer_from_dynamodb_items

    res = infer_from_dynamodb_items([{"a": 1}, {"a": 2}], return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"


def test_infer_from_firestore_requires_google_cloud_firestore() -> None:
    try:
        import google.cloud.firestore  # type: ignore  # noqa: F401
    except Exception:
        pytest.skip("google-cloud-firestore not installed")

    from infermodel.adapters import infer_from_firestore

    class FakeDoc:
        def __init__(self, d):
            self._d = d

        def to_dict(self):
            return self._d

    class FakeQuery:
        def stream(self):
            return iter([FakeDoc({"a": 1}), FakeDoc({"a": 2})])

    res = infer_from_firestore(FakeQuery(), return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"


def test_infer_from_redisjson_requires_redis() -> None:
    try:
        import redis  # noqa: F401
    except Exception:
        pytest.skip("redis not installed")

    from infermodel.adapters import infer_from_redisjson

    class FakeJson:
        def __init__(self, docs):
            self._docs = docs

        def get(self, key, path):
            return self._docs[key]

    class FakeClient:
        def __init__(self, docs):
            self._json = FakeJson(docs)

        def json(self):
            return self._json

    docs = {"k1": {"a": 1}, "k2": {"a": 2}}
    res = infer_from_redisjson(FakeClient(docs), ["k1", "k2"], return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"


def test_infer_from_couchdb_requires_couchdb() -> None:
    try:
        import couchdb  # noqa: F401
    except Exception:
        pytest.skip("couchdb not installed")

    from infermodel.adapters import infer_from_couchdb_view

    rows = [{"value": {"a": 1}}, {"value": {"a": 2}}]
    res = infer_from_couchdb_view(rows, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"

