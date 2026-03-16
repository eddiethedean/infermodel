"""Convert inferred schema dict into Pydantic models via create_model."""

from __future__ import annotations

from typing import Any, Union

from pydantic import create_model

from infermodel.schema import get_fields
from infermodel.typing_utils import schema_type_to_annotation


def model_from_schema(
    schema: dict[str, Any],
    model_name: str = "InferredModel",
) -> type:
    """
    Build a Pydantic model class from an inferred schema dict.

    The schema must have type "model" and a "fields" dict. Each field has
    "type", "required", and "nullable". Nested models are built recursively.
    """
    fields_spec = get_fields(schema)
    model_fields: dict[str, tuple[Any, Any]] = {}

    for name, field_spec in fields_spec.items():
        type_info = field_spec.get("type")
        # Nested model: build a concrete Pydantic model for this field.
        if isinstance(type_info, dict) and type_info.get("type") == "model":
            nested_schema: dict[str, Any] = {
                "type": "model",
                "fields": type_info.get("fields") or {},
            }
            nested_model_name = f"{model_name}_{name.capitalize()}"
            ann = model_from_schema(nested_schema, model_name=nested_model_name)
        else:
            ann = schema_type_to_annotation(field_spec)
        required = field_spec.get("required", True)
        nullable = field_spec.get("nullable", False)

        # Pydantic v2: (annotation, default). Use ... for required, None for optional/nullable.
        if not required or nullable:
            ann = Union[ann, None]
        if not required:
            default = None
        elif nullable:
            default = None
        else:
            default = ...
        model_fields[name] = (ann, default)

    return create_model(model_name, **model_fields)  # type: ignore[call-overload]
