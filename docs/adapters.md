# Adapters

infermodel’s core is format-agnostic: everything ultimately becomes an `Iterable[Mapping[str, Any]]` and is passed to `infer(...)`.

Adapters are **thin helpers** that:

- read a source (file / database / client)
- yield rows as dict-like mappings
- call `infer(...)`

The most important behavior to understand: **adapters stream** wherever possible, so `InferConfig.sample_size` limits how many rows are consumed from the source.

## General contract

- **Input**: adapters accept a source handle (path, file, engine, client, etc.)
- **Row**: each yielded row is a `Mapping[str, Any]` (usually a `dict`)
- **Streaming**: inference consumes up to `sample_size` rows, then stops consuming the iterator

## File / format adapters

### CSV — `infer_from_csv(...)`

- **Input**: a file path (`str | Path`) or an open `IO[str]`
- **Row shape**: `csv.DictReader` yields `dict[str, str]` (values are strings)
- **Tips**:
  - for typical CSVs with `"true"/"false"/"null"` etc. use `InferConfig.for_csv()`
  - pass delimiter/encoding via kwargs (e.g. `delimiter=";"`)

### JSON — `infer_from_json(...)`

- **Input**: file path or open `IO[str]`
- **Row shape**: the JSON must be an **array of objects**, each object must be a mapping
- **Notes**: this adapter loads the full JSON array into memory

### NDJSON — `infer_from_ndjson(...)`

- **Input**: file path or open `IO[str]`
- **Row shape**: one JSON object per non-empty line
- **Notes**: streaming; blank lines are ignored; non-object line raises `TypeError`

### Pandas — `infer_from_dataframe(...)` (optional extra)

- **Input**: `pandas.DataFrame`
- **Row shape**: yields dict records from `df.to_dict(orient="records")`
- **Streaming**:
  - if `chunk_size` is provided, iterates in chunks (still yields per-row dicts)

Install: `pip install "infermodel[pandas]"`

### Parquet — `infer_from_parquet(...)` (optional extra)

- **Input**: Parquet file path
- **Row shape**: yields dicts from pyarrow record batches (`batch.to_pylist()`)
- **Streaming**: iterates batches (`batch_size=...`)

Install: `pip install "infermodel[parquet]"`

## SQL adapters

### SQLAlchemy — `infer_from_sqlalchemy(engine_or_conn, selectable, ...)` (optional extra)

- **Input**:
  - `Engine` OR `Connection`
  - a SQLAlchemy Core selectable (e.g. `select(table)` or a text query)
- **Row shape**: uses `Result.mappings()` and yields `dict(row)`
- **Streaming**: stops reading after `sample_size` rows (because it streams mappings)

Install: `pip install "infermodel[sqlalchemy]"`

## NoSQL adapters

These are thin “best-effort” adapters: they assume the driver returns dict-like documents/items.

### MongoDB — `infer_from_mongodb(collection, ...)` (optional extra)

- **Input**: a `pymongo` collection-like object that supports `.find(...)`
- **Row shape**: documents yielded by the cursor; converted with `dict(doc)`
- **Gotcha**: Mongo documents typically include `_id` (often an ObjectId)

Install: `pip install "infermodel[mongodb]"`

### DynamoDB — `infer_from_dynamodb(table, ...)` / `infer_from_dynamodb_items(items, ...)` (optional extra)

- **Preferred**: `infer_from_dynamodb_items(items, ...)` when you already have Python dict items
- **Table adapter input**: a boto3 Table-like object supporting `.scan(...)` or `.query(...)`
- **Row shape**: yields each element of the response `Items` list as a dict
- **Streaming**: paginates using `LastEvaluatedKey`

Install: `pip install "infermodel[dynamodb]"`

### Firestore — `infer_from_firestore(query, ...)` (optional extra)

- **Input**: a Firestore query-like object with `.stream()`
- **Row shape**: yields `dict(doc.to_dict())` for each doc; docs returning `None` are skipped

Install: `pip install "infermodel[firestore]"`

### RedisJSON — `infer_from_redisjson(client, keys, ...)` (optional extra)

- **Input**: a redis client with `client.json().get(key, path)`
- **Row shape**: expects a mapping at `path` (or a single-element list containing a mapping); yields dicts

Install: `pip install "infermodel[redis]"`

### CouchDB — `infer_from_couchdb_view(view_result, ...)` (optional extra)

- **Input**: an iterable of row objects (commonly dicts) from a CouchDB view
- **Row shape**: reads `row[value_key]` (default `value`) and yields it if it’s a mapping

Install: `pip install "infermodel[couchdb]"`

## Local-only smoke tests

See `smoke/README.md` for local, best-effort smoke tests against real services (Dockerized Mongo + Redis, and SQLite via SQLAlchemy).

