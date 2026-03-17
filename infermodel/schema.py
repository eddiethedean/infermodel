"""Typed schema (v1) and helpers.

The Rust core returns a JSON-serializable "schema dict". In Python we provide a
typed representation to make the library easier to use and extend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence


SchemaVersion = Literal[1]

ScalarTypeTag = Literal[
    "any",
    "bool",
    "int",
    "float",
    "str",
    "date",
    "datetime",
    "time",
]


@dataclass(frozen=True)
class TypeSpec:
    """Base class for type specs."""


@dataclass(frozen=True)
class ScalarTypeSpec(TypeSpec):
    tag: ScalarTypeTag


@dataclass(frozen=True)
class ListTypeSpec(TypeSpec):
    item: TypeSpec


@dataclass(frozen=True)
class UnionTypeSpec(TypeSpec):
    variants: tuple[TypeSpec, ...]


@dataclass(frozen=True)
class ModelTypeSpec(TypeSpec):
    fields: Mapping[str, "FieldSpec"]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_spec: TypeSpec
    required: bool
    nullable: bool


@dataclass(frozen=True)
class SchemaModel:
    schema_version: SchemaVersion
    type: Literal["model"]
    fields: Mapping[str, FieldSpec]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "type": "model",
            "fields": {name: field_to_dict(f) for name, f in self.fields.items()},
        }


def schema_from_dict(schema: Mapping[str, Any]) -> SchemaModel:
    schema_version = schema.get("schema_version", 1)
    if schema_version != 1:
        raise ValueError(f"Unsupported schema_version: {schema_version!r}")
    if schema.get("type") != "model":
        raise ValueError("Schema must have type 'model'")
    raw_fields = schema.get("fields") or {}
    if not isinstance(raw_fields, Mapping):
        raise TypeError("Schema 'fields' must be a mapping")
    fields: dict[str, FieldSpec] = {}
    for name, raw_field in raw_fields.items():
        if not isinstance(name, str):
            raise TypeError("Schema field names must be strings")
        if not isinstance(raw_field, Mapping):
            raise TypeError(f"Field spec for {name!r} must be a mapping")
        fields[name] = field_from_dict(name, raw_field)
    return SchemaModel(schema_version=1, type="model", fields=fields)


def field_from_dict(name: str, field_spec: Mapping[str, Any]) -> FieldSpec:
    required = bool(field_spec.get("required", True))
    nullable = bool(field_spec.get("nullable", False))
    type_info = field_spec.get("type", "any")
    return FieldSpec(
        name=name,
        type_spec=type_spec_from_obj(type_info),
        required=required,
        nullable=nullable,
    )


def field_to_dict(field: FieldSpec) -> dict[str, Any]:
    return {
        "type": type_spec_to_obj(field.type_spec),
        "required": field.required,
        "nullable": field.nullable,
    }


def type_spec_from_obj(obj: Any) -> TypeSpec:
    # Scalar form: "int", "str", etc.
    if isinstance(obj, str):
        if obj not in {
            "any",
            "bool",
            "int",
            "float",
            "str",
            "date",
            "datetime",
            "time",
        }:
            return ScalarTypeSpec("any")
        return ScalarTypeSpec(obj)  # type: ignore[arg-type]

    # Structured form: {"type": "...", ...}
    if isinstance(obj, Mapping):
        kind = obj.get("type")
        if kind == "list":
            return ListTypeSpec(item=type_spec_from_obj(obj.get("item")))
        if kind == "union":
            variants_raw = obj.get("variants") or []
            if not isinstance(variants_raw, Sequence):
                raise TypeError("union variants must be a sequence")
            return UnionTypeSpec(tuple(type_spec_from_obj(v) for v in variants_raw))
        if kind == "model":
            raw_fields = obj.get("fields") or {}
            if not isinstance(raw_fields, Mapping):
                raise TypeError("model fields must be a mapping")
            fields: dict[str, FieldSpec] = {}
            for field_name, raw_field in raw_fields.items():
                if not isinstance(field_name, str):
                    raise TypeError("Nested field names must be strings")
                if not isinstance(raw_field, Mapping):
                    raise TypeError(f"Nested field spec for {field_name!r} must be a mapping")
                fields[field_name] = field_from_dict(field_name, raw_field)
            return ModelTypeSpec(fields=fields)

    return ScalarTypeSpec("any")


def type_spec_to_obj(spec: TypeSpec) -> Any:
    if isinstance(spec, ScalarTypeSpec):
        return spec.tag
    if isinstance(spec, ListTypeSpec):
        return {"type": "list", "item": type_spec_to_obj(spec.item)}
    if isinstance(spec, UnionTypeSpec):
        return {"type": "union", "variants": [type_spec_to_obj(v) for v in spec.variants]}
    if isinstance(spec, ModelTypeSpec):
        return {
            "type": "model",
            "fields": {name: field_to_dict(f) for name, f in spec.fields.items()},
        }
    return "any"
