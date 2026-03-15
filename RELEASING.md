# Releasing to PyPI

## CI (push / PR)

On push or PR to `main` or `master`, `.github/workflows/ci.yml` runs:

- **Python**: ruff format/check, mypy
- **Rust**: cargo fmt, clippy, cargo audit, cargo test (Linux/macOS/Windows)
- **Python tests**: pytest on 3.9–3.12 × Ubuntu/Windows/macOS (maturin develop + pytest)

## Release (tag)

Push a tag `v*` (e.g. `v0.1.0`) to trigger `.github/workflows/release.yml`:

1. Same checks as CI (format, clippy, audit, python-lint, python-tests).
2. On success, **publish to PyPI** with [maturin-action](https://github.com/messense/maturin-action):
   - manylinux x86_64 (+ sdist from that job)
   - manylinux aarch64
   - macOS x86_64 and aarch64
   - Windows x86_64

**Required:** Repository secret `PYPI_API_TOKEN` (PyPI API token).

```bash
git tag v0.1.0
git push origin v0.1.0
```

## One-off: build and publish from this machine

```bash
maturin build --release -o dist --interpreter python3.12
twine upload dist/*
# Or: maturin publish --no-sdist -i python3.12
```
