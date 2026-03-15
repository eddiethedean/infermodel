"""Schema dataclasses and helpers for the inferred spec (Python view)."""

from __future__ import annotations

from typing import Any


def get_fields(schema: dict[str, Any]) -> dict[str, Any]:
    """Return the 'fields' dict from a top-level model schema."""
    if schema.get("type") != "model":
        raise ValueError("Schema must have type 'model'")
    return schema.get("fields") or {}
