"""Public API: infer_schema and infer_model."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import infermodel._infermodel as _infermodel
from infermodel.config import InferConfig
from infermodel.emit_pydantic import model_from_schema


def infer_schema(
    data: Iterable[Mapping[str, Any]],
    config: InferConfig | None = None,
) -> dict[str, Any]:
    """
    Infer a schema from an iterable of mappings (e.g. list of dicts, generator).

    Returns a nested dict with:
      - "type": "model"
      - "fields": { field_name: { "type", "required", "nullable" }, ... }

    At most config.sample_size items are used for inference (default 10,000; 0 = no limit).

    Args:
        data: Iterable of mappings (rows), e.g. list, tuple, or generator of dicts.
        config: Optional inference config (default policies if None).

    Returns:
        Schema dict suitable for introspection or model_from_schema().

    Raises:
        TypeError: If input is not an iterable of mappings, or mapping keys are not strings.
        ValueError: For policy/config-related errors (e.g. strict policy conflicts).
    """
    _config = config if config is not None else InferConfig()
    return _infermodel.infer_schema(
        data,
        infer_string_numbers=_config.infer_string_numbers,
        infer_string_literals=_config.infer_string_literals,
        incompatible_scalar_policy=_config.incompatible_scalar_policy,
        heterogeneous_list_policy=_config.heterogeneous_list_policy,
        dict_mixed_policy=_config.dict_mixed_policy,
        string_date_policy=_config.string_date_policy,
        numeric_promotion=_config.numeric_promotion,
        missing_key_policy=_config.missing_key_policy,
        null_policy=_config.null_policy,
        sample_size=_config.sample_size,
    )


def infer_model(
    data: Iterable[Mapping[str, Any]],
    model_name: str = "InferredModel",
    config: InferConfig | None = None,
) -> type:
    """
    Infer a schema from data and return a dynamic Pydantic model.

    This is a convenience wrapper around ``infer_schema`` + ``model_from_schema``:
    nested dict fields become nested Pydantic models; scalar and nullable/optional
    behavior follow the same rules as the inferred schema.

    Args:
        data: Iterable of mappings (e.g. list of dicts or generator) to infer schema from.
        model_name: Name for the generated model class.
        config: Optional inference config; controls string parsing, policies, and sample_size.

    Returns:
        A Pydantic model class (type) that can validate the inferred shape.
    """
    schema = infer_schema(data, config=config)
    return model_from_schema(schema, model_name=model_name)
