# Roadmap: 0.1.0 → 1.0.0

Plan from current state to a production-ready 1.0.0 release.

---

## Current state (0.1.0, Alpha)

- **API**: `infer_schema(data, config=None)`, `infer_model(data, model_name=..., config=None)`, `model_from_schema(schema, model_name=...)`
- **Input**: `Iterable[Mapping[str, Any]]`; inference capped at `config.sample_size` (default 10,000; 0 = no limit)
- **Config**: `InferConfig(infer_string_numbers=True, infer_string_literals=False, sample_size=10_000)`
- **Inference**: Flat + **nested dict** inference; scalar types (int, float, bool, str, Any); required/optional and nullable; int+float → float; string→number and optional string→null/bool; dict+non-dict conflicts → Any (default policy)
- **Emission**: Schema dict → Pydantic v2 model via `emit_pydantic`, including nested models
- **CI**: Ruff, mypy, cargo fmt, clippy, audit, pytest on Python 3.9–3.12 (Ubuntu, macOS, Windows)
- **Release**: Tag `v*` triggers PyPI publish (manylinux, macOS, Windows); see [RELEASING.md](RELEASING.md)

---

## 1.0.0 scope (production release)

1.0.0 is **stable, documented, and safe to rely on** for the current feature set. It does **not** require every possible feature from the original plan (see [plandoc.md](plandoc.md)); it requires:

- **Stable public API** (no breaking changes planned for 1.x after 1.0)
- **Clear documentation** (README, API behavior, limits, upgrade path)
- **Packaging and release hygiene** (version, classifiers, changelog)
- **No known blocking bugs** for typical flat and nested use cases

**Explicitly in scope for 1.0**

- Flat schema inference and Pydantic emission as implemented today
- **Nested dict → nested model inference** (dict values become nested Pydantic models; recursive inference and emission)
- Iterable + `sample_size` behavior
- `infer_string_numbers` / `infer_string_literals` behavior
- Required vs optional vs nullable semantics

**Explicitly out of scope for 1.0** (candidates for 1.1+)

- List type inference (e.g. `list[int]`, `list[Model]`)
- Date/datetime/time inference
- Additional policy options (beyond current config)
- Performance benchmarks and published numbers

---

## Milestones

**Order and dependencies**: M0 → M1 → M2 → M3 (sequential). M4 is optional and can run in parallel with M1–M2 so tests and CI are solid before release.

### M0 — Nested struct support (required for 1.0)

- [x] **Rust inference**: When a field value is a dict, recursively infer a nested `ModelSpec`. Use `TypeSpec::Model(nested)` instead of treating dict as `Any`. Merge multiple dict observations by merging nested model specs (field-by-field).
- [x] **Rust merge**: Implement merge for `TypeSpec::Model` (merge two ModelSpecs by merging each field’s type; dict + non-dict → `Any` per existing policy).
- [x] **Schema output**: Ensure serialization emits nested `{"type": "model", "fields": {...}}` for nested models.
- [x] **Python emission**: Emit nested Pydantic models for fields with `type: { "type": "model", "fields": ... }` (built recursively via `model_from_schema`) and use them as annotations (not `Any`).
- [x] **Tests**: Add tests for one-level and multi-level nested dicts; optional/nullable nested; mixed dict + scalar.

**Exit criterion**: `infer_schema` / `infer_model` support nested dicts end-to-end; nested Pydantic models validate correctly.

---
---

### M1 — Stability and API lock (pre-1.0)

- [x] **API review**: Freeze public surface (e.g. `infer_schema`, `infer_model`, `InferConfig`, `model_from_schema`); document what is stable vs internal
- [x] **Edge-case tests**: Empty iterable, single row, all-None column, very large `sample_size`; document expected behavior
- [x] **Error contract**: Document which errors (ValueError, TypeError, etc.) can be raised and when; add minimal tests for error paths
- [ ] **Deprecations**: If any names or signatures might change, introduce deprecation path before 1.0

Additional M1 work completed:

- [x] **Nested required semantics**: Nested keys missing from some observed nested dicts are treated as optional (`required=False`), matching top-level semantics.

**Exit criterion**: Team agrees the current API is 1.0-ready and no breaking change is planned for 1.0.

---

### M2 — Documentation

- [x] **README**: Ensure README and pyproject match implementation (Iterable, sample_size, nested, config options) and Quick start / API / config sections are accurate
- [x] **Limitations**: One short section on what is not inferred in 1.0 (lists, dates) and how to handle them (manual schema or post-process)
- [x] **Changelog**: Add `CHANGELOG.md`; maintain from 0.1.0 onward (or link to GitHub Releases)
- [x] **API reference**: Either in README or via Sphinx/autodoc; at minimum, docstrings for public functions and `InferConfig` are accurate and complete

**Exit criterion**: A new user can install, run the quick start, and understand what the library does and does not do.

---

### M3 — Packaging and release hygiene

- [ ] **Version and classifiers**: Set version to `1.0.0` for release; update classifiers (e.g. `Development Status :: 5 - Production/Stable`) when cutting 1.0
- [ ] **RELEASING.md**: Confirm steps for tagging and PyPI; ensure `PYPI_API_TOKEN` and any secrets are documented for maintainers
- [ ] **Git tag and release**: Tag `v1.0.0`, push, verify workflow publishes to PyPI; create GitHub Release with short release notes
- [ ] **Post-release**: After 1.0.0 is published, branch or tag policy for 1.x patches (e.g. maintain `1.0.x` for security/fixes)

**Exit criterion**: 1.0.0 is on PyPI and installable with `pip install infermodel==1.0.0`; release is documented.

---

### M4 — Optional but recommended before 1.0

Can be done in parallel with M1–M2. Ensures quality and compatibility before tagging 1.0.

- [ ] **Rust tests**: Add or expand Rust unit tests so that core inference (classify, merge, required/nullable, nested) is covered without Python
- [ ] **Security**: Run `cargo audit` in CI (already in place); address any advisories before 1.0
- [ ] **Python 3.9**: Keep 3.9 in CI matrix; test on 3.9 explicitly so we do not accidentally drop support at 1.0

**Exit criterion**: No known blockers; CI green on all supported platforms and Python versions.

---

## After 1.0.0

- **1.1.x**: List type inference, date/datetime/time support (see plandoc phases 4, 7)
- **1.x**: Policy options and tuning (e.g. more merge policies) as needed
- **Changelog**: Maintain CHANGELOG or Releases for every minor/patch release

See **Future ideas** below for a detailed backlog (Pydantic alignment, outliers, ergonomics, etc.).

---

## Future ideas (post-1.0)

Backlog of features that fit the package; not committed to a release. Prioritize based on demand.

### Inference & types

- **List inference** — Infer `list[int]`, `list[str]`, `list[Model]`; empty list → `list[Any]` or configurable. (Rust has `TypeSpec::List`; wire classify + merge.)
- **Date / datetime / time** — Infer from real Python `date`/`datetime`/`time`; optional opt-in string→date parsing (e.g. ISO).
- **Union inference** — When a field mixes incompatible types (e.g. int | str), emit `Union[...]` instead of `Any`, or make it policy (union vs any vs error). (Rust has `TypeSpec::Union`; wire merge.)
- **Decimal** — Recognize `Decimal`; optional string→Decimal for money/scientific columns.
- **Literal / enum inference** — If a string field has a small fixed set of values, infer `Literal["a","b","c"]` or suggest Enum.
- **UUID** — Treat `uuid.UUID` or UUID-like strings as a dedicated type or `str` with validator.
- **Outliers tolerance (optional)** — Config option e.g. `outliers=0.1` (10%): when inferring a field’s type, allow up to that fraction of values to “not match” the chosen type; infer the **majority** type and treat the rest as outliers (ignored for inference). Example: column values `'1','2',…,'9','Q'` with `outliers=0.1` → infer `int` (9/10 match). **Must be optional**: it deliberately breaks the normal guarantee that every sampled row validates against the inferred model—rows with outlier values will fail validation. Use for noisy data where you want a “clean” schema and are willing to reject bad rows. Implementation: per-field type counts; if minority count ≤ outliers × total, use majority type; else keep current merge (Any/union).

### Schema & emission

- **JSON Schema export** — From inferred schema → JSON Schema for OpenAPI, form generators, other languages.
- **OpenAPI-friendly output** — Ensure inferred models give good `model_json_schema()` or provide a helper for OpenAPI-ready schema.
- **Schema diff / evolution** — Compare two inferred schemas (e.g. old vs new sample), report added/removed/changed types for drift checks.
- **Minimal vs strict preset** — Option to infer “minimal” (e.g. more optional) vs “strict” (required when present in all rows) for different use cases.
- **Force all fields optional or required** — Optional config (e.g. `require_all=True` or `optional_all=True`) to override inferred required/optional: emit every field as required (no default) or every field as optional (default `None`), regardless of presence in the sample. Useful for strict validation or permissive ingestion without changing inference logic.

### Performance & scale

- **Sampling strategies** — Besides “first N”, support random sample or stratified (e.g. by a key) for more representative inference.
- **Streaming / chunked inference** — For huge iterables, merge schema from chunks so we don’t materialize the full sample at once.
- **Benchmarks** — Small benchmark suite (e.g. `benches/`) vs pure-Python or naive inference; optional note in README.

### Ergonomics

- **Named presets** — e.g. `InferConfig.pragmatic()`, `InferConfig.strict()`, `InferConfig.for_csv()` that set `infer_string_numbers`, `infer_string_literals`, etc. in one call.
- **Field rename / exclude** — Optional mapping or blocklist so the emitted model has different names or drops sensitive columns.
- **Validation-only mode** — “Does this data match this schema?” without building a new model; reuse inferred schema + validation path.
- **Pretty-print schema** — `infermodel.print_schema(schema)` or similar for quick terminal inspection.

### Integrations

- **TypedDict / Protocol emission** — Option to emit `TypedDict` or `Protocol` instead of (or alongside) Pydantic model for static typing without runtime validation.

### Adapter layer (data-source agnostic, format helpers)

**Principle**: Core stays format-agnostic (`Iterable[Mapping[str, Any]]` only). Adapters are thin helpers that convert a format-specific input → iterable of dicts → `infer_schema` / `infer_model`. Optional dependencies per adapter keep the base install minimal; streaming where possible (yield rows, respect `sample_size`).

- **JSON** — `infer_schema_from_json(path_or_file, config=...)` / `infer_model_from_json(...)`: parse JSON array (or stream) → iterable of dicts → core. Support single JSON array and optionally NDJSON (newline-delimited) for streaming.
- **CSV** — `infer_schema_from_csv(path_or_file, config=...)` / `infer_model_from_csv(...)`: e.g. `csv.DictReader` → iterable of dicts → core. Stdlib only; no extra deps. Option for delimiter, encoding.
- **NDJSON / JSON Lines** — Can be part of JSON adapter (detect or flag): one JSON object per line → yield dicts → core; good for large files.
- **Pandas** — `infer_schema_from_dataframe(df, config=...)` / `infer_model_from_dataframe(df, ...)`: `df.to_dict('records')` or chunked iteration → iterable of dicts → core. Optional extra `[pandas]`.
- **Parquet** — `infer_schema_from_parquet(path_or_file, config=...)` / `infer_model_from_parquet(...)`: read via pyarrow or pandas in chunks → iterable of dicts → core. Optional extra `[parquet]` (pyarrow or pandas).
- **Extras in pyproject** — e.g. `infermodel[csv]` (stdlib-only, no new deps), `infermodel[pandas]`, `infermodel[parquet]` so users only pull what they need; base package remains dependency-light.

**Exit criterion**: Every common format has a one-liner to “infer from this source” without the core knowing about the format; all adapters document that they pass through `config` (including `sample_size`).

### Pydantic alignment

Features to align infermodel’s inferred types and emitted models with Pydantic’s supported types and APIs. Reference: [Pydantic v2 types](https://docs.pydantic.dev/2.9/usage/types/types/), [standard library types](https://docs.pydantic.dev/2.9/api/standard_library_types/), [Field API](https://docs.pydantic.dev/2.9/api/fields/).

#### Types Pydantic supports that we should infer/emit

- **date, datetime, time** — We have `TypeSpec::Date/DateTime/Time` and classify Python `date`/`datetime`/`time`; emit `datetime.date`, `datetime.datetime`, `datetime.time` in annotations (not `Any`). Optional: opt-in string→date/datetime parsing (ISO, Unix timestamp).
- **timedelta** — Classify and emit `datetime.timedelta`; Pydantic accepts str (e.g. `'1d,01:02:03'`) and ISO duration.
- **Decimal** — Classify `Decimal`; emit `Decimal`; optional string→Decimal for numeric-looking strings.
- **UUID** — Classify `uuid.UUID` or UUID-like strings (opt-in); emit `UUID`; Pydantic accepts str/bytes and validates.
- **bytes** — Classify and emit `bytes`; Pydantic accepts str (encode), bytearray, int/float/Decimal (str(v).encode()).
- **Literal** — When a string field has a small, fixed set of observed values, emit `Literal["a","b","c"]` instead of `str`; improves validation and JSON schema.
- **Enum** — When values are a small fixed set (str or int), optionally emit a dynamic `str, Enum` or `IntEnum` subclass; Pydantic validates membership.
- **list, tuple, set** — Infer and emit `list[T]`, `tuple[T,...]`, `set[T]`; we already have `TypeSpec::List`; add tuple/set classification if needed.
- **Dict[str, V]** — For dict values we infer nested model; Pydantic also supports `Dict[str, int]` etc.; optional emit for “all values same type” dicts.
- **pathlib.Path** — Classify and emit `Path` when values are path-like (or opt-in).
- **Strict types** — Config option to emit `StrictInt`, `StrictFloat`, `StrictStr`, `StrictBool` so Pydantic does not coerce (e.g. no str→int); matches “strict mode” use cases.

#### Field() metadata we could infer and pass through

- **description** — Optional per-field description (e.g. from column name, or empty); pass to `Field(description=...)` when building model.
- **title** — Human-readable title; default to field name; `Field(title=...)`.
- **min_length / max_length** — For str (and list): compute from observed lengths; emit `Field(min_length=..., max_length=...)` or `Annotated[str, Len(min_length=..., max_length=...)]` (annotated-types).
- **ge / le / gt / lt** — For int/float: compute from observed min/max; emit `Field(ge=..., le=...)` or `Annotated[int, Gt(0)]` etc.; improves validation and JSON schema.
- **multiple_of** — If all observed numbers are multiples of a divisor (e.g. 0.01 for currency), emit `Field(multiple_of=...)`.
- **pattern** — Only if we add regex detection (advanced); `Field(pattern=...)` for str.
- **examples** — Sample values from the data; `Field(examples=[...])` for docs/OpenAPI.
- **alias** — When emitting, support a name→alias map so `Field(alias=...)` or `validation_alias` is set (e.g. camelCase from API).

#### Model-level and schema behavior

- **model_config** — Option to emit `model_config = ConfigDict(strict=True)` or `extra='forbid'` etc. via preset (e.g. `InferConfig.strict()` → strict model).
- **JSON Schema / OpenAPI** — Emitted models already have `model_json_schema()`; ensure nested models, Literal, and Field constraints produce correct JSON schema; optional helper `infermodel.schema_to_json_schema(schema)` for the raw inferred schema.
- **Serialization** — Ensure emitted types round-trip with `model_dump(mode='json')` (date/datetime/time/Decimal/UUID → JSON-friendly form per Pydantic behavior).
- **Discriminated union** — If we infer a union of nested models with a common “tag” field, consider emitting `Field(discriminator='tag')` for efficient validation (advanced).

#### Constrained types (Pydantic / annotated-types)

- **conint, confloat, condecimal** — Instead of plain int/float/Decimal, emit `Annotated[int, Field(ge=..., le=...)]` or use `annotated_types` (Gt, Ge, Lt, Le, Len) so Pydantic and JSON schema get constraints.
- **constr** — For str with min/max length or pattern, emit `Annotated[str, Field(min_length=..., max_length=..., pattern=...)]` or constr equivalent.

---

## Summary

| Milestone | Focus | When |
|-----------|--------|------|
| **M0** | Nested struct inference + Pydantic emission (required for 1.0) | First |
| **M1** | API stability, edge cases, errors | After M0 |
| **M2** | Docs, limitations, changelog | After M1 |
| **M3** | Version 1.0.0, PyPI publish, release notes | After M2 |
| **M4** | Tests and CI polish (optional, recommended before 1.0) | In parallel with M1–M2 |

**Target**: 1.0.0 = production-ready for **flat and nested** schema inference and Pydantic emission, with clear docs and a stable API. List/date features can follow in 1.1+.
