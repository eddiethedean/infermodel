# infermodel

Rust-backed schema inference from `Iterable[Mapping]` data (e.g. list of dicts, generators) with Pydantic model emission.

Infer a schema from an iterable of mappings (e.g. list, tuple, or generator of dicts), then convert that inferred schema into a Pydantic model on the Python side—without hardcoding schema logic in application code. By default at most 10,000 items are used for inference; set `config.sample_size` to change this (0 = no limit).

## Features

- **Rust core**: Performance-critical traversal, merge logic, and required/nullable tracking
- **Python ergonomics**: Pydantic v2 model creation via `infer_model(...)`
- **Number inference from strings (default)**: String columns that look like numbers are inferred as `int` or `float` (e.g. `"42"`, `"3.14"`). Set `infer_string_numbers=False` to keep all strings as `str`.
- **Optional null/bool from strings**: Set `infer_string_literals=True` to treat `"null"`/`"true"`/`"false"`/`"yes"`/`"no"` as null or bool (for full CSV/JSON-style parsing).
- **Numeric promotion**: int+float promotes to float; incompatible scalar mixes become `Any`
- **Required vs nullable**: Tracks presence (missing key → optional) and explicit `None` (nullable) separately

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
- **Native types**: Python `int`, `float`, `bool`, `None`, list, and dict are always classified by type; date/datetime/time objects are recognized when present.

## Required vs nullable

- **Required**: field present in every row.
- **Optional**: field missing in at least one row.
- **Nullable**: at least one row had explicit `None` for that field.

These are independent: a field can be required and nullable, or optional and not nullable.

## Development

```bash
# Create venv and install in editable mode with Rust extension
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
maturin develop

# Run tests
pytest
```

## License

MIT
