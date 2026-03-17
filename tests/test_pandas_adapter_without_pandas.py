from __future__ import annotations

import sys
import types

import pytest

from infermodel.adapters import infer_from_dataframe


def test_infer_from_dataframe_chunking_without_real_pandas(monkeypatch: pytest.MonkeyPatch) -> None:
    # Provide a minimal pandas stub so we can exercise adapter branches without pandas installed.
    pandas = types.ModuleType("pandas")

    class DataFrame:
        def __init__(self, rows):
            self._rows = list(rows)

        def to_dict(self, orient="records"):
            assert orient == "records"
            return list(self._rows)

        def __len__(self):
            return len(self._rows)

        @property
        def iloc(self):
            df = self

            class _ILoc:
                def __getitem__(self, slc):
                    return DataFrame(df._rows[slc])

            return _ILoc()

    pandas.DataFrame = DataFrame  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pandas", pandas)

    df = DataFrame([{"a": 1}, {"a": 2}, {"a": 3}])
    res = infer_from_dataframe(df, return_model=False)
    assert res.schema_dict is not None
    assert res.schema_dict["fields"]["a"]["type"] == "int"

    res2 = infer_from_dataframe(df, return_model=False, chunk_size=2)
    assert res2.schema_dict is not None
    assert res2.schema_dict["fields"]["a"]["type"] == "int"

    with pytest.raises(ValueError):
        infer_from_dataframe(df, return_model=False, chunk_size=0)

    with pytest.raises(TypeError):
        infer_from_dataframe({"not": "df"}, return_model=False)  # type: ignore[arg-type]

