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

    @classmethod
    def for_csv(cls, *, sample_size: int = 10_000) -> "InferConfig":
        """
        Preset for typical CSV/DictReader inputs:
        - parse number-like strings
        - parse null/bool-like strings
        """
        return cls(infer_string_numbers=True, infer_string_literals=True, sample_size=sample_size)

    @classmethod
    def permissive(cls, *, sample_size: int = 10_000) -> "InferConfig":
        """Preset that prefers 'any' over errors/unions in conflicts."""
        return cls(
            incompatible_scalar_policy="any",
            heterogeneous_list_policy="any",
            dict_mixed_policy="any",
            numeric_promotion="promote",
            infer_string_numbers=True,
            infer_string_literals=False,
            sample_size=sample_size,
        )

    @classmethod
    def strict(cls, *, sample_size: int = 10_000) -> "InferConfig":
        """
        Preset for stricter inference:
        - numeric_promotion strict (int+float doesn't silently promote)
        - dict/non-dict conflicts raise
        - incompatible scalars raise
        """
        return cls(
            incompatible_scalar_policy="error",
            heterogeneous_list_policy="error",
            dict_mixed_policy="error",
            numeric_promotion="strict",
            infer_string_numbers=True,
            infer_string_literals=False,
            sample_size=sample_size,
        )
