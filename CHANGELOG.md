# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nested dict → nested model inference implemented in the Rust core and emitted as nested Pydantic v2 models.
- Policy-driven behavior for incompatible scalars, heterogeneous lists, and dict/non-dict mixes (configurable via `InferConfig`).
- Standardized error contract: `TypeError` for invalid input shapes (non-iterables, bad mappings, invalid policy strings) and `ValueError` for policy/config errors.
- Expanded robust test suite covering nested models, policies, edge cases, and error paths.
- Documentation updates to README and public docstrings to reflect nested behavior and policies.

## [0.1.0] - Initial release

### Added
- Rust-backed schema inference for flat models from `Iterable[Mapping[str, Any]]`.
- Basic scalar type inference (int, float, bool, str, Any) with number-string parsing and required/nullable tracking.
- Pydantic v2 model emission via `infer_model` and `model_from_schema`.
- Initial configuration surface via `InferConfig` (string-number and string-literal parsing, sampling).
- CI, packaging, and test setup.

