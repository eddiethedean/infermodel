from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from infermodel.adapters.parquet_ import infer_from_parquet


def test_infer_from_parquet_file_not_found_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Stub pyarrow.parquet so import guard passes.
    pyarrow = types.ModuleType("pyarrow")
    parquet = types.ModuleType("pyarrow.parquet")

    class ParquetFile:
        def __init__(self, path):
            self.path = path

        def iter_batches(self, batch_size=1000):
            return iter([])

    parquet.ParquetFile = ParquetFile  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pyarrow", pyarrow)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", parquet)

    missing = tmp_path / "missing.parquet"
    with pytest.raises(FileNotFoundError):
        infer_from_parquet(missing, return_model=False)

