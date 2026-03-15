"""Public API: infer_schema and infer_model."""

from __future__ import annotations

from typing import Any

from infermodel import _infermodel
from infermodel.config import InferConfig
from infermodel.emit_pydantic import model_from_schema


def infer_schema(
    data: list[dict[str, Any]],
    config: InferConfig | None = None,
) -> dict[str, Any]:
    """
    Infer a schema from Python list[dict] data.

    Returns a nested dict with:
      - "type": "model"
      - "fields": { field_name: { "type", "required", "nullable" }, ... }

    Args:
        data: List of dicts (rows) to infer schema from.
        config: Optional inference config (default policies if None).

    Returns:
        Schema dict suitable for introspection or model_from_schema().
    """
    _config = config if config is not None else InferConfig()
    return _infermodel.infer_schema(data)


def infer_model(
    data: list[dict[str, Any]],
    model_name: str = "InferredModel",
    config: InferConfig | None = None,
) -> type:
    """
    Infer a schema from data and return a dynamic Pydantic model.

    Args:
        data: List of dicts to infer schema from.
        model_name: Name for the generated model class.
        config: Optional inference config.

    Returns:
        A Pydantic model class (type) that can validate the inferred shape.
    """
    schema = infer_schema(data, config=config)
    return model_from_schema(schema, model_name=model_name)
