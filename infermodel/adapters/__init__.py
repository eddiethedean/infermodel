"""Format adapters (thin helpers) for infermodel.

Core infermodel stays data-source agnostic: it infers from Iterable[Mapping[str, Any]].
Adapters provide convenient loaders that yield row-mappings for common formats.
"""

from __future__ import annotations

from infermodel.adapters.csv_ import infer_from_csv
from infermodel.adapters.couchdb_ import infer_from_couchdb_view
from infermodel.adapters.dynamodb_ import infer_from_dynamodb, infer_from_dynamodb_items
from infermodel.adapters.firestore_ import infer_from_firestore
from infermodel.adapters.json_ import infer_from_json, infer_from_ndjson
from infermodel.adapters.mongodb_ import infer_from_mongodb
from infermodel.adapters.pandas_ import infer_from_dataframe
from infermodel.adapters.parquet_ import infer_from_parquet
from infermodel.adapters.redisjson_ import infer_from_redisjson
from infermodel.adapters.sqlalchemy_ import infer_from_sqlalchemy

__all__ = [
    "infer_from_csv",
    "infer_from_couchdb_view",
    "infer_from_dynamodb",
    "infer_from_dynamodb_items",
    "infer_from_firestore",
    "infer_from_json",
    "infer_from_ndjson",
    "infer_from_mongodb",
    "infer_from_dataframe",
    "infer_from_parquet",
    "infer_from_redisjson",
    "infer_from_sqlalchemy",
]

