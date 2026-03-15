"""Python config wrappers for inference policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class InferConfig:
    """
    Configuration for schema inference behavior.

    V1 uses built-in policy values; future versions may support
    named presets (e.g. strict, pragmatic, api_friendly).
    """

    incompatible_scalar_policy: Literal["any", "union", "error"] = "any"
    heterogeneous_list_policy: Literal["any", "union", "error"] = "any"
    dict_mixed_policy: Literal["any", "union", "error"] = "any"
    string_date_policy: Literal["never", "iso_only", "aggressive"] = "never"
    numeric_promotion: Literal["promote", "strict"] = "promote"
    missing_key_policy: Literal["optional"] = "optional"
    null_policy: Literal["nullable"] = "nullable"
