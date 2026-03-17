from __future__ import annotations

import json

import io
import sys
import types

import pytest

from infermodel import InferConfig
from infermodel.adapters import infer_from_csv, infer_from_json, infer_from_ndjson


def _stub_module(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    if name in sys.modules:
        return
    monkeypatch.setitem(sys.modules, name, types.ModuleType(name))


def test_infer_from_csv(tmp_path) -> None:
    p = tmp_path / "data.csv"
    p.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
    res = infer_from_csv(p, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"
    assert res.schema_dict["fields"]["name"]["type"] == "str"

    # File-object branch + custom delimiter
    p2 = tmp_path / "data2.csv"
    p2.write_text("id;name\n1;Alice\n", encoding="utf-8")
    with p2.open("r", encoding="utf-8", newline="") as f:
        res2 = infer_from_csv(f, return_model=False, delimiter=";")
    assert res2.schema_dict is not None
    assert res2.schema_dict["fields"]["id"]["type"] == "int"


def test_infer_from_json(tmp_path) -> None:
    p = tmp_path / "data.json"
    p.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    res = infer_from_json(p, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"

    # Non-list JSON is rejected
    p2 = tmp_path / "bad.json"
    p2.write_text(json.dumps({"id": 1}), encoding="utf-8")
    with pytest.raises(TypeError):
        infer_from_json(p2, return_model=False)
    # file-object branch
    res3 = infer_from_json(io.StringIO(json.dumps([{"id": 1}])), return_model=False)
    assert res3.schema_dict is not None
    with pytest.raises(TypeError):
        infer_from_json(io.StringIO(json.dumps([1])), return_model=False)


def test_infer_from_ndjson(tmp_path) -> None:
    p = tmp_path / "data.ndjson"
    p.write_text('{"id": "1"}\n\n{"id": "2"}\n', encoding="utf-8")
    res = infer_from_ndjson(
        p,
        config=InferConfig(infer_string_numbers=True),
        return_model=False,
    )
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["id"]["type"] == "int"

    p_bad = tmp_path / "bad.ndjson"
    p_bad.write_text('"not an object"\n', encoding="utf-8")
    with pytest.raises(TypeError):
        infer_from_ndjson(p_bad, return_model=False)
    # file-object branch
    res2 = infer_from_ndjson(io.StringIO('{"id": 1}\n'), return_model=False)
    assert res2.schema_dict is not None


def test_infer_from_dataframe_requires_pandas() -> None:
    # If pandas isn't installed in the environment, simulate it so we can still
    # cover the adapter logic without requiring the dependency.
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

    with pytest.raises(ValueError):
        infer_from_parquet(p, return_model=False, batch_size=0)


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

    with engine.connect() as conn:
        res2 = infer_from_sqlalchemy(conn, select(users), return_model=False)
        assert res2.schema_dict is not None
        assert res2.schema_dict["fields"]["id"]["type"] == "int"


def test_infer_from_mongodb_requires_pymongo() -> None:
    # Do not require pymongo installed: stub it so import guard passes.
    from infermodel.adapters import infer_from_mongodb

    monkeypatch = pytest.MonkeyPatch()
    try:
        _stub_module(monkeypatch, "pymongo")

        class NonMappingDoc:
            def __iter__(self):
                return iter([("a", 1)])

        class FakeCollection:
            def find(self, *args, **kwargs):
                return iter([{"a": 1}, NonMappingDoc()])

        res = infer_from_mongodb(FakeCollection(), return_model=False, find_kwargs={"batch_size": 10})
        assert res.schema_dict is not None
        assert res.schema_dict["fields"]["a"]["type"] in {"int", "any"}
    finally:
        monkeypatch.undo()


def test_infer_from_dynamodb_requires_boto3() -> None:
    from infermodel.adapters import infer_from_dynamodb_items

    monkeypatch = pytest.MonkeyPatch()
    try:
        _stub_module(monkeypatch, "boto3")

        res = infer_from_dynamodb_items([{"a": 1}, {"a": 2}], return_model=False)
        assert res.schema_dict is not None
        assert res.schema_dict["fields"]["a"]["type"] == "int"

        # Pagination branch via fake table (does not require AWS)
        from infermodel.adapters import infer_from_dynamodb

        class FakeTable:
            def __init__(self):
                self.calls = 0

            def scan(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return {"Items": [{"a": 1}], "LastEvaluatedKey": {"k": "v"}}
                return {"Items": [{"a": 2}]}

        schema = infer_from_dynamodb(FakeTable(), return_model=False).schema_dict
        assert schema is not None
        assert schema["fields"]["a"]["type"] == "int"

        with pytest.raises(ValueError):
            infer_from_dynamodb(FakeTable(), mode="nope")  # type: ignore[arg-type]

    finally:
        monkeypatch.undo()


def test_infer_from_firestore_requires_google_cloud_firestore() -> None:
    from infermodel.adapters import infer_from_firestore

    monkeypatch = pytest.MonkeyPatch()
    try:
        _stub_module(monkeypatch, "google")
        _stub_module(monkeypatch, "google.cloud")
        _stub_module(monkeypatch, "google.cloud.firestore")

        class FakeDoc:
            def __init__(self, d):
                self._d = d

            def to_dict(self):
                return self._d

        class FakeQuery:
            def stream(self):
                return iter([FakeDoc({"a": 1}), FakeDoc({"a": 2}), FakeDoc(None)])

        res = infer_from_firestore(FakeQuery(), return_model=False)
        assert res.schema_dict is not None
        assert res.schema_dict["fields"]["a"]["type"] == "int"

    finally:
        monkeypatch.undo()


def test_infer_from_redisjson_requires_redis() -> None:
    from infermodel.adapters import infer_from_redisjson

    monkeypatch = pytest.MonkeyPatch()
    try:
        _stub_module(monkeypatch, "redis")

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

        # list-wrapped doc branch
        docs2 = {"k1": [{"a": 1}], "k2": [{"a": 2}]}
        res2 = infer_from_redisjson(FakeClient(docs2), ["k1", "k2"], return_model=False)
        assert res2.schema_dict is not None
        assert res2.schema_dict["fields"]["a"]["type"] == "int"

        # else branch: non-mapping doc is ignored
        docs3 = {"k1": 1, "k2": 2}
        res3 = infer_from_redisjson(FakeClient(docs3), ["k1", "k2"], return_model=False)
        assert res3.schema_dict is not None
        assert res3.schema_dict["fields"] == {}
    finally:
        monkeypatch.undo()


def test_infer_from_couchdb_requires_couchdb() -> None:
    from infermodel.adapters import infer_from_couchdb_view

    monkeypatch = pytest.MonkeyPatch()
    try:
        _stub_module(monkeypatch, "couchdb")

        rows = [{"value": {"a": 1}}, {"value": {"a": 2}}]
        res = infer_from_couchdb_view(rows, return_model=False)
        assert res.schema_dict is not None
        assert res.schema_dict["fields"]["a"]["type"] == "int"

        # fallback path: row[value_key] (row is Mapping)
        rows2 = [{"doc": {"a": 1}}, {"doc": {"a": 2}}]
        res2 = infer_from_couchdb_view(rows2, value_key="doc", return_model=False)
        assert res2.schema_dict is not None
        assert res2.schema_dict["fields"]["a"]["type"] == "int"

        # row is not Mapping but supports __getitem__
        class RowObj:
            def __init__(self, d):
                self._d = d

            def __getitem__(self, key):
                return self._d[key]

        res_obj = infer_from_couchdb_view([RowObj({"value": {"a": 3}})], return_model=False)
        assert res_obj.schema_dict is not None
        assert res_obj.schema_dict["fields"]["a"]["type"] == "int"

        # else branch: row is not Mapping and raises in __getitem__
        class BadRow:
            def __getitem__(self, key):
                raise KeyError(key)

        res3 = infer_from_couchdb_view([BadRow()], value_key="doc", return_model=False)
        assert res3.schema_dict is not None
        assert res3.schema_dict["fields"] == {}

    finally:
        monkeypatch.undo()

