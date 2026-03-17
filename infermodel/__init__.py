"""
infermodel: Rust-backed schema inference from Iterable[Mapping] with Pydantic model emission.

Infer a schema from an iterable of mappings (e.g. list of dicts, generators) using a Rust core,
then convert that inferred schema into a Pydantic model on the Python side.
"""

from infermodel.config import InferConfig
from infermodel.emit_pydantic import model_from_schema
from infermodel.infer import InferResult, infer, infer_iter, infer_iter_rows
from infermodel.schema_tools import format_schema, print_schema, schema_diff, schema_merge

__all__ = [
    "infer",
    "infer_iter",
    "infer_iter_rows",
    "InferResult",
    "model_from_schema",
    "InferConfig",
    "format_schema",
    "print_schema",
    "schema_diff",
    "schema_merge",
]
