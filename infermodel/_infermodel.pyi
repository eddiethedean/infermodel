"""Stub for Rust extension _infermodel."""

from typing import Any

def infer_schema(
    data: Any,
    *,
    infer_string_numbers: bool = ...,
    infer_string_literals: bool = ...,
    incompatible_scalar_policy: str = ...,
    heterogeneous_list_policy: str = ...,
    dict_mixed_policy: str = ...,
    string_date_policy: str = ...,
    numeric_promotion: str = ...,
    missing_key_policy: str = ...,
    null_policy: str = ...,
    sample_size: int = ...,
) -> Any: ...


def infer_schema_with_diagnostics(
    data: Any,
    *,
    infer_string_numbers: bool = ...,
    infer_string_literals: bool = ...,
    incompatible_scalar_policy: str = ...,
    heterogeneous_list_policy: str = ...,
    dict_mixed_policy: str = ...,
    string_date_policy: str = ...,
    numeric_promotion: str = ...,
    missing_key_policy: str = ...,
    null_policy: str = ...,
    sample_size: int = ...,
) -> Any: ...
