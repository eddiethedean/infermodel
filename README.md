# infermodel

**Rust-backed schema inference from any iterable of dict-like rows → Pydantic v2 models.**

Infer a schema from `Iterable[Mapping[str, Any]]` (list of dicts, generators, etc.), then get an introspectable schema dict or a dynamic Pydantic model—no hand-written schemas. Data-source agnostic: pass whatever yields rows of dicts; optional adapter helpers for JSON, CSV, Parquet, and Pandas are [planned](ROADMAP.md#adapter-layer-data-source-agnostic-format-helpers). By default at most 10,000 rows are used for inference; set `config.sample_size` to change this (0 = no limit).

## Features

- **Rust core**: Performance-critical traversal, merge logic, and required/nullable tracking
- **Python ergonomics**: Pydantic v2 model creation via `infer_model(...)` (including nested models)
- **Number inference from strings (default)**: String columns that look like numbers are inferred as `int` or `float` (e.g. `"42"`, `"3.14"`). Set `infer_string_numbers=False` to keep all strings as `str`.
- **Optional null/bool from strings**: Set `infer_string_literals=True` to treat `"null"`/`"true"`/`"false"`/`"yes"`/`"no"` as null or bool (for full CSV/JSON-style parsing).
- **Numeric promotion**: int+float promotes to float; incompatible scalar mixes become `Any`
- **Required vs nullable**: Tracks presence (missing key → optional) and explicit `None` (nullable) separately
- **Sampling**: Use first N rows (default 10k) so large streams and generators are safe and fast

## Installation

From the project root (with a virtualenv activated):

```bash
pip install -e .
# or: maturin develop
```

Requirements: Python 3.9+, Pydantic v2. Build requires Rust (for the extension).

## Quick start

```python
from infermodel import infer_schema, infer_model

data = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": None},
    {"id": 3},  # missing "name" -> optional
]

# Get introspectable schema dict
schema = infer_schema(data)
# {"type": "model", "fields": {"id": {"type": "int", "required": True, "nullable": False}, ...}}

# Get a Pydantic model class
Model = infer_model(data, model_name="Record")
instance = Model(id=1, name="Alice")
```

By default, number-like strings (`"42"`, `"3.14"`) are inferred as int/float. For CSV with boolean or null-like strings, set `infer_string_literals=True`:

```python
import csv, io
from infermodel import infer_model, InferConfig

raw = "id,name,active\n1,Alice,true\n2,Bob,false"
rows = list(csv.DictReader(io.StringIO(raw)))
# id and active get int/bool when infer_string_literals=True
Model = infer_model(rows, model_name="User", config=InferConfig(infer_string_literals=True))
```

## API

- **`infer_schema(data, config=None)`**  
  Returns a nested dict with `type`, `fields`, and per-field `type`, `required`, `nullable`.

- **`infer_model(data, model_name="InferredModel", config=None)`**  
  Infers the schema and returns a dynamic Pydantic model class.

- **`InferConfig`**  
  **`infer_string_numbers=True`** (default): infer int/float from string content. **`infer_string_literals=False`** (default): set to `True` to infer null/bool from `"null"`/`"true"`/`"false"`/`"yes"`/`"no"`. **`sample_size=10_000`**: max number of items to use for inference (0 = no limit); use a larger value or 0 for very large iterables when you want to sample more or all rows.

- **`model_from_schema(schema, model_name="InferredModel")`**  
  Build a Pydantic model from an existing schema dict (e.g. from `infer_schema`).

## Type inference

- **Number strings (default)**: String values that parse as integers or floats are inferred as `int` or `float` (e.g. `"42"`, `"3.14"`). Set `infer_string_numbers=False` to keep every string as `str`.
- **Null/bool strings (opt-in)**: With **`infer_string_literals=True`**:
  - **Null-like**: `"null"`, `"none"`, `"nil"` (case-insensitive) → treated as null (column is nullable).
  - **Boolean-like**: `"true"`, `"false"`, `"yes"`, `"no"` → `bool`.
  That mode is not round-trip compatible for those columns (the model expects parsed types).
- **Native types**: Python `int`, `float`, `bool`, `None` are classified by type. Dict values are inferred as **nested models** (recursive `model` specs) and emitted as nested Pydantic models. List values are currently treated as `Any`. Date/datetime/time objects are recognized when present but emitted as `Any` for now.

## Required vs nullable

- **Required**: field present in every row.
- **Optional**: field missing in at least one row.
- **Nullable**: at least one row had explicit `None` for that field.

These are independent: a field can be required and nullable, or optional and not nullable. The same rules apply inside **nested models**: nested fields that are missing in some observed nested dicts become optional, and nested fields that see `None` at least once become nullable.

## Limitations

- **Lists**: List values are inferred as `Any`; `list[T]` inference is planned for 1.1+.
- **Dates**: Real `date`/`datetime`/`time` objects are detected but the emitted type is `Any`; proper types and string parsing are planned.

For full scope and future work (adapters, Pydantic alignment, outliers), see [ROADMAP.md](ROADMAP.md).

## Development

```bash
# Create venv and install in editable mode with Rust extension
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
maturin develop

# Run tests
pytest
```

## Links

- [Roadmap](ROADMAP.md) — 1.0 plan, nested structs, adapter layer, Pydantic alignment
- [Repository](https://github.com/eddiethedean/infermodel)

## License

MIT
