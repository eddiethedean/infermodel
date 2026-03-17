# infermodel roadmap

This roadmap is intentionally **product-oriented**: it describes what a user can do, what guarantees we provide, and the minimal set of work required to ship a trustworthy 1.0.

The project already has a lot of surface area (typed schema, diagnostics, adapters, streaming helpers). The goal from here is not to add more features—it’s to make what exists **reliable, predictable, and clearly documented**.

---

## North Star (what “infermodel” should feel like)

Given any source that can produce rows as `Mapping[str, Any]`, a user should be able to:

- **Infer once** from a representative sample
- **Inspect** a stable schema (`schema_version: 1`)
- **Validate/clean** a stream of rows into Pydantic models
- **Understand decisions** via diagnostics
- **Adopt incrementally** via adapters and schema merge/diff tools

The library should be boring in production: stable API, consistent contracts, strong tests, and clear failure modes.

---

## Public surface (1.0 contract)

### Primary entrypoint

- `infer(data, *, config=None, model_name="InferredModel", return_model=True, return_schema=True, return_diagnostics=False) -> InferResult`
  - **Guarantee**: `InferResult.schema_dict` is JSON-serializable and includes `schema_version: 1`.

### Streaming validation

- `infer_iter(...) -> (InferResult, iterator[Model])`
- `infer_iter_rows(...) -> (InferResult, iterator[(row, model_or_none, error_or_none)])`

### Schema + tools

- Typed schema objects + stable dict contract
- `format_schema`, `print_schema`, `schema_diff`, `schema_merge`

### Adapters (optional extras)

Thin helpers that yield rows and delegate to `infer(...)`:

- Files/formats: CSV, JSON, NDJSON, Pandas, Parquet
- SQL: SQLAlchemy
- NoSQL: MongoDB, DynamoDB, Firestore, RedisJSON, CouchDB

---

## What 1.0.0 means

**1.0.0 is not “feature complete”.** It is:

- A **stable contract**: API signatures, schema dict shape, and error semantics
- **Predictable behavior** on typical real-world flat/nested data
- **Portable packaging**: wheels across supported platforms
- **Strong tests** + coverage gate + CI confidence
- Documentation that makes onboarding easy

### Explicitly in scope for 1.0

- Flat + nested dict inference
- Required/optional/nullable semantics
- String parsing toggles (`infer_string_numbers`, `infer_string_literals`)
- Diagnostics output (stable keys and semantics)
- Streaming validation helpers
- Adapter layer + optional dependency extras

### Explicitly out of scope for 1.0 (1.1+)

- List element inference (`list[T]`)
- Date/datetime/time inference and parsing
- Benchmark suite + published perf numbers

---

## Milestones (big picture)

### M0 — Foundation (done)

- [x] Core inference works for flat + nested
- [x] Typed schema v1 exists and round-trips
- [x] Pydantic emission works for nested models

### M1 — Contracts (done)

- [x] Public API consolidated around `infer(...)`
- [x] Clear error contract (TypeError vs ValueError) and policy behavior
- [x] High branch coverage gate in CI

### M2 — Production hardening (next)

Focus: make behavior rock-solid across adapters and real inputs.

- **Adapter reliability**:
  - [x] Document each adapter’s row shape expectations (e.g. DynamoDB resource vs low-level client) — see [`docs/adapters.md`](docs/adapters.md)
  - [x] Add “real backend smoke tests” (Dockerized Mongo/Redis; SQLite via SQLAlchemy) and a short guide to run them locally — see [`smoke/README.md`](smoke/README.md)
- **Diagnostics contract**:
  - [x] Document fields and semantics (especially `maybe_truncated` and per-field counts) — see [`docs/diagnostics.md`](docs/diagnostics.md)
  - [x] Add tests that freeze the diagnostics shape (stable keys + semantics)
- **Edge-case policy tests**:
  - [ ] Ensure policies behave consistently across nested models and unions

Exit: no known correctness bugs from real-world trial runs.

### M3 — 1.0 packaging + release

- [ ] Set version to `1.0.0`
- [ ] Update classifiers to Production/Stable
- [ ] Tag + publish via existing GitHub Actions
- [ ] Create a GitHub Release with concise notes and upgrade guidance

Exit: `pip install infermodel==1.0.0` works everywhere in CI matrix.

---

## Post‑1.0 direction

### 1.1 — Better types

- List element inference (`list[T]`, `list[Model]`)
- Date/datetime/time emission (and optional string parsing)
- Optional: emit unions instead of `any` in more cases

### 1.x — Ecosystem & ergonomics

- JSON Schema / OpenAPI helpers
- Schema drift tooling (diff reports, compatibility checks)
- More presets and stricter model configs

---

## Quality bar

- **Branch coverage**: keep CI gate at **≥97%** (raise over time if practical)
- **CI green** across Python 3.9–3.12 and OS matrix
- **No silent contract changes**: any schema dict changes require a version bump (e.g. `schema_version=2`)
