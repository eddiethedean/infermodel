"""Primary public API: infer(...) returning a rich result object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

import infermodel._infermodel as _infermodel
from infermodel.config import InferConfig
from infermodel.emit_pydantic import model_from_schema
from infermodel.schema import SchemaModel, schema_from_dict


@dataclass(frozen=True)
class InferResult:
    """Result of inference: typed schema, dict schema, optional model, optional diagnostics."""

    schema: Optional[SchemaModel]
    schema_dict: Optional[dict[str, Any]]
    model: Optional[type]
    diagnostics: Optional[dict[str, Any]]


def infer(
    data: Iterable[Mapping[str, Any]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer a schema (and optionally a Pydantic model) from an iterable of mappings.

    This is the primary entrypoint for infermodel.
    """
    _config = config if config is not None else InferConfig()

    if return_diagnostics:
        out: dict[str, Any] = _infermodel.infer_schema_with_diagnostics(
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
        raw_schema = out["schema"]
        diagnostics = out.get("diagnostics")
    else:
        raw_schema = _infermodel.infer_schema(
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
        diagnostics = None

    # Enforce schema v1 wrapper even if Rust doesn't emit it yet.
    schema_dict = dict(raw_schema)
    schema_dict.setdefault("schema_version", 1)

    schema_obj = schema_from_dict(schema_dict)

    model = model_from_schema(schema_obj, model_name=model_name) if return_model else None

    return InferResult(
        schema=schema_obj if return_schema else None,
        schema_dict=schema_obj.to_dict() if return_schema else None,
        model=model,
        diagnostics=diagnostics,
    )

