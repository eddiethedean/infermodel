"""Python config wrappers for inference policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class InferConfig:
    """
    Configuration for schema inference behavior.

    By default, number strings ("42", "3.14") are inferred as int/float.
    Set infer_string_literals=True to also infer "null"/"true"/"false"/"yes"/"no" from strings.
    """

    incompatible_scalar_policy: Literal["any", "union", "error"] = "any"
    heterogeneous_list_policy: Literal["any", "union", "error"] = "any"
    dict_mixed_policy: Literal["any", "union", "error"] = "any"
    string_date_policy: Literal["never", "iso_only", "aggressive"] = "never"
    numeric_promotion: Literal["promote", "strict"] = "promote"
    missing_key_policy: Literal["optional"] = "optional"
    null_policy: Literal["nullable"] = "nullable"
    # Infer int/float from string content (default True).
    infer_string_numbers: bool = True
    # Infer null and bool from "null"/"true"/"false"/"yes"/"no" (default False).
    infer_string_literals: bool = False
