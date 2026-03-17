"""Small UX helpers for working with inferred schemas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from infermodel.schema import (
    FieldSpec,
    ListTypeSpec,
    ModelTypeSpec,
    ScalarTypeSpec,
    SchemaModel,
    TypeSpec,
    UnionTypeSpec,
    schema_from_dict,
)


def format_schema(schema: Any) -> str:
    """Pretty-format a schema (SchemaModel or schema dict) into a readable tree."""
    s = schema if isinstance(schema, SchemaModel) else schema_from_dict(schema)
    lines: List[str] = [f"Schema(v{s.schema_version}): model"]
    for name in sorted(s.fields.keys()):
        _format_field(lines, field=s.fields[name], indent=0)
    return "\n".join(lines)


def print_schema(schema: Any) -> None:
    """Print a schema using format_schema()."""
    print(format_schema(schema))


def _format_field(lines: List[str], *, field: FieldSpec, indent: int) -> None:
    req = "required" if field.required else "optional"
    nul = "nullable" if field.nullable else "non-null"
    prefix = "  " * indent + f"- {field.name}: {req}, {nul}, "
    _format_type(lines, prefix=prefix, spec=field.type_spec, indent=indent)


def _format_type(lines: List[str], *, prefix: str, spec: TypeSpec, indent: int) -> None:
    if isinstance(spec, ScalarTypeSpec):
        lines.append(prefix + spec.tag)
        return
    if isinstance(spec, ListTypeSpec):
        lines.append(prefix + "list[")
        _format_type(lines, prefix=("  " * (indent + 1) + "- item: "), spec=spec.item, indent=indent + 1)
        lines.append("  " * indent + "]")
        return
    if isinstance(spec, UnionTypeSpec):
        lines.append(prefix + "union")
        for v in spec.variants:
            _format_type(lines, prefix=("  " * (indent + 1) + "- "), spec=v, indent=indent + 1)
        return
    if isinstance(spec, ModelTypeSpec):
        lines.append(prefix + "model")
        for name in sorted(spec.fields.keys()):
            _format_field(lines, field=spec.fields[name], indent=indent + 1)
        return
    lines.append(prefix + "any")


@dataclass(frozen=True)
class SchemaChange:
    path: str
    kind: str  # added_field | removed_field | changed_type | changed_required | changed_nullable
    before: Optional[Any] = None
    after: Optional[Any] = None


def schema_diff(a: Any, b: Any) -> List[SchemaChange]:
    """Return a list of changes required to go from schema a -> schema b."""
    sa = a if isinstance(a, SchemaModel) else schema_from_dict(a)
    sb = b if isinstance(b, SchemaModel) else schema_from_dict(b)
    changes: List[SchemaChange] = []
    _diff_models(changes, path="", a_fields=sa.fields, b_fields=sb.fields)
    return changes


def _diff_models(
    out: List[SchemaChange],
    *,
    path: str,
    a_fields: Mapping[str, FieldSpec],
    b_fields: Mapping[str, FieldSpec],
) -> None:
    a_keys = set(a_fields.keys())
    b_keys = set(b_fields.keys())
    for k in sorted(a_keys - b_keys):
        out.append(SchemaChange(path=_join(path, k), kind="removed_field", before=_field_summary(a_fields[k])))
    for k in sorted(b_keys - a_keys):
        out.append(SchemaChange(path=_join(path, k), kind="added_field", after=_field_summary(b_fields[k])))
    for k in sorted(a_keys & b_keys):
        af = a_fields[k]
        bf = b_fields[k]
        if af.required != bf.required:
            out.append(
                SchemaChange(
                    path=_join(path, k),
                    kind="changed_required",
                    before=af.required,
                    after=bf.required,
                )
            )
        if af.nullable != bf.nullable:
            out.append(
                SchemaChange(
                    path=_join(path, k),
                    kind="changed_nullable",
                    before=af.nullable,
                    after=bf.nullable,
                )
            )
        if _type_sig(af.type_spec) != _type_sig(bf.type_spec):
            out.append(
                SchemaChange(
                    path=_join(path, k),
                    kind="changed_type",
                    before=_type_sig(af.type_spec),
                    after=_type_sig(bf.type_spec),
                )
            )
        # recurse into nested models if both are models
        if isinstance(af.type_spec, ModelTypeSpec) and isinstance(bf.type_spec, ModelTypeSpec):
            _diff_models(out, path=_join(path, k), a_fields=af.type_spec.fields, b_fields=bf.type_spec.fields)


def schema_merge(a: Any, b: Any) -> Dict[str, Any]:
    """
    Merge two schemas into a single schema dict.

    This is a Python-side merge helper intended for incremental/batch inference when you
    already have two schemas (e.g. infer first chunk, infer next chunk, merge).
    """
    sa = a if isinstance(a, SchemaModel) else schema_from_dict(a)
    sb = b if isinstance(b, SchemaModel) else schema_from_dict(b)
    merged = SchemaModel(schema_version=1, type="model", fields=_merge_models(sa.fields, sb.fields))
    return merged.to_dict()


def _merge_models(a: Mapping[str, FieldSpec], b: Mapping[str, FieldSpec]) -> Dict[str, FieldSpec]:
    out: Dict[str, FieldSpec] = {}
    keys = set(a.keys()) | set(b.keys())
    for k in keys:
        if k in a and k in b:
            fa = a[k]
            fb = b[k]
            out[k] = FieldSpec(
                name=k,
                type_spec=_merge_types(fa.type_spec, fb.type_spec),
                required=(fa.required and fb.required),
                nullable=(fa.nullable or fb.nullable),
            )
        elif k in a:
            # if missing from one side, mark optional
            fa = a[k]
            out[k] = FieldSpec(name=k, type_spec=fa.type_spec, required=False, nullable=fa.nullable)
        else:
            fb = b[k]
            out[k] = FieldSpec(name=k, type_spec=fb.type_spec, required=False, nullable=fb.nullable)
    return out


def _merge_types(a: TypeSpec, b: TypeSpec) -> TypeSpec:
    if _type_sig(a) == _type_sig(b):
        return a

    # nested models: merge recursively
    if isinstance(a, ModelTypeSpec) and isinstance(b, ModelTypeSpec):
        return ModelTypeSpec(fields=_merge_models(a.fields, b.fields))

    # scalar numeric promotion: int+float -> float
    if isinstance(a, ScalarTypeSpec) and isinstance(b, ScalarTypeSpec):
        if {a.tag, b.tag} == {"int", "float"}:
            return ScalarTypeSpec("float")
        return ScalarTypeSpec("any")

    # unions: normalize by signatures
    variants: List[TypeSpec] = []
    if isinstance(a, UnionTypeSpec):
        variants.extend(list(a.variants))
    else:
        variants.append(a)
    if isinstance(b, UnionTypeSpec):
        variants.extend(list(b.variants))
    else:
        variants.append(b)
    # de-dupe
    seen = set()
    uniq: List[TypeSpec] = []
    for v in variants:
        sig = _type_sig(v)
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(v)
    return UnionTypeSpec(tuple(uniq))


def _type_sig(spec: TypeSpec) -> Any:
    if isinstance(spec, ScalarTypeSpec):
        return ("scalar", spec.tag)
    if isinstance(spec, ListTypeSpec):
        return ("list", _type_sig(spec.item))
    if isinstance(spec, UnionTypeSpec):
        return ("union", tuple(sorted((_type_sig(v) for v in spec.variants), key=str)))
    if isinstance(spec, ModelTypeSpec):
        # structural signature
        return (
            "model",
            tuple(sorted((k, _field_summary(v)) for k, v in spec.fields.items())),
        )
    return ("scalar", "any")


def _field_summary(f: FieldSpec) -> Any:
    return {
        "required": f.required,
        "nullable": f.nullable,
        "type": _type_sig(f.type_spec),
    }


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key

