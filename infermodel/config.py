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

    Policy fields (e.g. dict_mixed_policy, numeric_promotion) are passed through to the Rust core.
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
    # Max number of items to use for inference when data is an iterable (default 10_000). 0 = no limit.
    sample_size: int = 10_000
