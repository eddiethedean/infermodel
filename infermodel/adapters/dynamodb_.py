from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_dynamodb_items(
    items: Iterable[Mapping[str, Any]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer from DynamoDB items already materialized as Python dicts.

    This is the most robust path if you already use boto3's resource API
    (which returns normal Python dicts).
    """
    return infer(
        items,
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )


def infer_from_dynamodb(
    table: Any,
    *,
    mode: str = "scan",
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
    operation_kwargs: Optional[Mapping[str, Any]] = None,
) -> InferResult:
    """
    Infer from a DynamoDB table using boto3 (optional dependency).

    Uses `table.scan(...)` or `table.query(...)` and paginates to stream items.
    """
    try:
        import boto3  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "boto3 is required for infer_from_dynamodb. Install with `pip install infermodel[dynamodb]`."
        ) from e

    operation_kwargs = dict(operation_kwargs or {})
    if mode not in {"scan", "query"}:
        raise ValueError("mode must be 'scan' or 'query'")

    def rows() -> Iterable[Mapping[str, Any]]:
        op = table.scan if mode == "scan" else table.query
        resp = op(**operation_kwargs)
        for item in resp.get("Items", []) or []:
            yield dict(item)
        while "LastEvaluatedKey" in resp:
            operation_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            resp = op(**operation_kwargs)
            for item in resp.get("Items", []) or []:
                yield dict(item)

    return infer(
        rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

