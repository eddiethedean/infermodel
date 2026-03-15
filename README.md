# infermodel

Rust-backed schema inference from `Sequence[Mapping]` data (e.g. list of dicts) with Pydantic model emission.

Infer a schema from a sequence of mappings (e.g. list or tuple of dicts), then convert that inferred schema into a Pydantic model on the Python side—without hardcoding schema logic in application code.

## Features

- **Rust core**: Performance-critical traversal, merge logic, and required/nullable tracking
- **Python ergonomics**: Pydantic v2 model creation via `infer_model(...)`
- **Conservative defaults**: Strings stay strings; int+float promotes to float; incompatible mixes become `Any`
- **Required vs nullable**: Tracks presence (missing key → optional) and explicit `None` (nullable) separately

## Installation

From the project root (with a virtualenv activated):

```bash
pip install -e .
# or: maturin develop
```

Requirements: Python 3.10+, Pydantic v2. Build requires Rust (for the extension).

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

## API

- **`infer_schema(data, config=None)`**  
  Returns a nested dict with `type`, `fields`, and per-field `type`, `required`, `nullable`.

- **`infer_model(data, model_name="InferredModel", config=None)`**  
  Infers the schema and returns a dynamic Pydantic model class.

- **`InferConfig`**  
  Dataclass for policy options (e.g. `incompatible_scalar_policy`, `string_date_policy`). V1 uses built-in policies only.

- **`model_from_schema(schema, model_name="InferredModel")`**  
  Build a Pydantic model from an existing schema dict (e.g. from `infer_schema`).

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
