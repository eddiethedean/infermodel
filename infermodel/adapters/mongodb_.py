from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_mongodb(
    collection: Any,
    *,
    filter: Optional[Mapping[str, Any]] = None,
    projection: Optional[Mapping[str, Any]] = None,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
    find_kwargs: Optional[Mapping[str, Any]] = None,
) -> InferResult:
    """
    Infer from a MongoDB collection using pymongo (optional dependency).

    Streams documents via `collection.find(...)`.
    """
    try:
        import pymongo  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "pymongo is required for infer_from_mongodb. Install with `pip install infermodel[mongodb]`."
        ) from e

    find_kwargs = dict(find_kwargs or {})
    cursor = collection.find(filter or {}, projection, **find_kwargs)

    def rows() -> Iterable[Mapping[str, Any]]:
        for doc in cursor:
            if isinstance(doc, Mapping):
                yield dict(doc)
            else:
                yield dict(doc)  # best-effort for bson-like docs

    return infer(
        rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

