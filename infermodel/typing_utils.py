"""Build Python type annotations from schema spec."""

from __future__ import annotations

import typing
from typing import Any

if typing.TYPE_CHECKING:
    pass


def schema_type_to_annotation(field_spec: dict[str, Any]) -> Any:
    """
    Convert a field spec dict (type, required, nullable) into a Python type annotation.

    Handles scalars (str, int, float, bool, date, datetime, time, any),
    list (with item type), and model (nested).
    """
    type_info = field_spec.get("type")

    if isinstance(type_info, str):
        return _scalar_to_annotation(type_info)
    if isinstance(type_info, dict):
        return _compound_to_annotation(type_info)
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


def _compound_to_annotation(type_info: dict[str, Any]) -> Any:
    kind = type_info.get("type")
    if kind == "list":
        item = type_info.get("item")
        if isinstance(item, str):
            item_ann = _scalar_to_annotation(item)
        elif isinstance(item, dict):
            item_ann = _compound_to_annotation(item)
        else:
            item_ann = Any
        return list[item_ann]  # type: ignore[valid-type]
    if kind == "model":
        # Nested model: we build dynamically in emit_pydantic
        return typing.Any  # Placeholder; actual nested model built there
    if kind == "union":
        variants = type_info.get("variants", [])
        if not variants:
            return Any
        anns = []
        for v in variants:
            if isinstance(v, str):
                anns.append(_scalar_to_annotation(v))
            elif isinstance(v, dict):
                anns.append(_compound_to_annotation(v))
            else:
                anns.append(Any)
        if len(anns) == 1:
            return anns[0]
        return typing.Union[tuple(anns)]  # type: ignore[valid-type]
    return Any
