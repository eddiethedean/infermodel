"""Build Python type annotations from typed schema specs."""

from __future__ import annotations

import typing
from typing import Any

from infermodel.schema import (
    ListTypeSpec,
    ModelTypeSpec,
    ScalarTypeSpec,
    TypeSpec,
    UnionTypeSpec,
)


def type_spec_to_annotation(spec: TypeSpec) -> Any:
    """Convert a TypeSpec into a Python type annotation."""
    if isinstance(spec, ScalarTypeSpec):
        return _scalar_to_annotation(spec.tag)
    if isinstance(spec, ListTypeSpec):
        item_ann = type_spec_to_annotation(spec.item)
        return list[item_ann]  # type: ignore[valid-type]
    if isinstance(spec, UnionTypeSpec):
        if not spec.variants:
            return Any
        anns = [type_spec_to_annotation(v) for v in spec.variants]
        if len(anns) == 1:
            return anns[0]
        return typing.Union[tuple(anns)]  # type: ignore[valid-type]
    if isinstance(spec, ModelTypeSpec):
        # Nested models are built dynamically in emit_pydantic.
        return typing.Any
    return Any


def _scalar_to_annotation(tag: str) -> Any:
    mapping = {
        "any": Any,
        "bool": bool,
        "int": int,
        "float": float,
        "str": str,
        "date": typing.Any,  # datetime.date
        "datetime": typing.Any,  # datetime.datetime
        "time": typing.Any,  # datetime.time
    }
    return mapping.get(tag, Any)
