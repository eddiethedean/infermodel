"""Format adapters (thin helpers) for infermodel.

Core infermodel stays data-source agnostic: it infers from Iterable[Mapping[str, Any]].
Adapters provide convenient loaders that yield row-mappings for common formats.
"""

from __future__ import annotations

from infermodel.adapters.csv_ import infer_from_csv
from infermodel.adapters.json_ import infer_from_json, infer_from_ndjson
from infermodel.adapters.pandas_ import infer_from_dataframe
from infermodel.adapters.parquet_ import infer_from_parquet

__all__ = [
    "infer_from_csv",
    "infer_from_json",
    "infer_from_ndjson",
    "infer_from_dataframe",
    "infer_from_parquet",
]

