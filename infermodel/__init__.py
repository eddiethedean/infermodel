"""
infermodel: Rust-backed schema inference from list[dict] with Pydantic model emission.

Infer a schema from Python list[dict] data using a Rust core, then convert that
inferred schema into a Pydantic model on the Python side.
"""

from infermodel.api import infer_schema, infer_model
from infermodel.config import InferConfig

__all__ = [
    "infer_schema",
    "infer_model",
    "InferConfig",
]
