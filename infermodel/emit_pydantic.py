"""Convert typed schema (or schema dict) into Pydantic models via create_model."""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional, Union

from pydantic import ConfigDict, Field, create_model

from infermodel.schema import (
    FieldSpec,
    ModelTypeSpec,
    SchemaModel,
    TypeSpec,
    schema_from_dict,
)
from infermodel.typing_utils import type_spec_to_annotation


def model_from_schema(
    schema: Any,
    model_name: str = "InferredModel",
    *,
    alias_by_path: Optional[Mapping[str, str]] = None,
    model_config: Optional[ConfigDict] = None,
) -> type:
    """
    Build a Pydantic model class from an inferred schema dict.

    The schema must have type "model" and a "fields" dict. Each field has
    "type", "required", and "nullable". Nested models are built recursively.
    """
    schema_obj = schema if isinstance(schema, SchemaModel) else schema_from_dict(schema)
    alias_by_path = alias_by_path or {}

    def build_model(
        *,
        schema_model: SchemaModel,
        root_name: str,
        path: tuple[str, ...],
    ) -> type:
        model_fields: dict[str, tuple[Any, Any]] = {}
        for field_name, field in schema_model.fields.items():
            field_path = ".".join((*path, field_name))
            ann = _annotation_for_field(field, root_name=root_name, path=(*path, field_name))

            # Pydantic v2: (annotation, default). Use ... for required, None for optional/nullable.
            if not field.required or field.nullable:
                ann = Union[ann, None]

            if not field.required or field.nullable:
                default = None
            else:
                default = ...

            alias = alias_by_path.get(field_path)
            if alias is not None:
                default = Field(default, alias=alias)

            model_fields[field_name] = (ann, default)

        cfg = model_config if (path == () and model_config is not None) else None
        return create_model(
            _safe_model_name(root_name if path == () else _nested_model_name(root_name, path)),
            __config__=cfg,
            **model_fields,
        )  # type: ignore[call-overload]

    def _annotation_for_field(field: FieldSpec, *, root_name: str, path: tuple[str, ...]) -> Any:
        ts = field.type_spec
        if isinstance(ts, ModelTypeSpec):
            nested_schema = SchemaModel(schema_version=1, type="model", fields=ts.fields)
            return build_model(schema_model=nested_schema, root_name=root_name, path=path)
        return type_spec_to_annotation(ts)

    return build_model(schema_model=schema_obj, root_name=model_name, path=())


_NON_IDENT = re.compile(r"[^0-9a-zA-Z_]")


def _safe_model_name(name: str) -> str:
    cleaned = _NON_IDENT.sub("_", name).strip("_")
    return cleaned or "InferredModel"


def _nested_model_name(root_name: str, path: tuple[str, ...]) -> str:
    # Use path segments to avoid collisions across nested models.
    parts = [_safe_model_name(root_name)] + [_safe_model_name(p).capitalize() for p in path]
    return "_".join(parts)
