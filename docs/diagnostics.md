# Diagnostics

When you call `infer(..., return_diagnostics=True)`, the returned `InferResult.diagnostics` explains what inference observed and whether sampling may have truncated the dataset.

This page defines the **stable diagnostics contract** (keys + semantics). Treat any other keys as non-contractual.

## Top-level keys

`diagnostics` is a `dict[str, Any]` with:

- **`rows_used`** (`int`): number of rows actually consumed from the input iterable during inference.
- **`sample_size`** (`int`): the configured sample size used for inference (from `InferConfig.sample_size`).
  - if `sample_size > 0`, inference will consume **at most** `sample_size` rows
  - if `sample_size == 0`, inference will consume **all** rows (for single-pass iterables, this means buffering)
- **`maybe_truncated`** (`bool`): `True` when `sample_size > 0` and inference consumed `sample_size` rows.
  - this indicates inference *may* have truncated the dataset (there could be more rows)
  - `False` means inference did not hit the sampling limit
- **`fields`** (`dict[str, FieldDiagnostics]`): evidence collected per field name.

## Per-field keys (`FieldDiagnostics`)

For each field name `k`, `diagnostics["fields"][k]` is a dict with:

- **`presence_count`** (`int`): number of observed rows that contained the key.
- **`missing_count`** (`int`): computed as `rows_used - presence_count`.
- **`null_count`** (`int`): number of observed rows where the value was explicitly `None`.
- **`type_counts`** (`dict[str, int]`): bucket counts by value “class”.

### `type_counts` buckets

Bucket names are strings produced by the Rust classifier. The contract is:

- values are **non-negative integers**
- keys are **strings**
- keys may vary by runtime input and by future versions (e.g. new buckets could appear)

You should write code and tests that assert **presence of expected buckets** (e.g. `"Int"`, `"Str"`, `"None"`, `"Dict"`) rather than asserting an exact set.

## Example

```python
from infermodel import InferConfig, infer

data = [
    {"a": 1, "b": None},
    {"a": 2},
    {"a": "oops", "b": {"x": 1}},
]

res = infer(data, return_model=False, return_diagnostics=True, config=InferConfig(sample_size=2))
diag = res.diagnostics

assert diag["rows_used"] == 2
assert diag["sample_size"] == 2
assert diag["maybe_truncated"] is True

# Field evidence only reflects the 2 rows that were used:
assert diag["fields"]["a"]["presence_count"] == 2
assert diag["fields"]["b"]["presence_count"] == 1
assert diag["fields"]["b"]["null_count"] == 1
```

## Notes on streaming

- `return_diagnostics=True` does **not** change schema inference behavior; it just returns evidence that inference already observed.
- Adapters that stream from backends (SQLAlchemy, MongoDB, DynamoDB pagination, RedisJSON fetch loop, NDJSON) will be affected by sampling: `rows_used` will typically equal `min(sample_size, available_rows)`.

