from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_firestore(
    query: Any,
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer from a Firestore query using google-cloud-firestore (optional dependency).

    Streams documents via `query.stream()`, yielding `doc.to_dict()`.
    """
    try:
        import google.cloud.firestore  # type: ignore  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "google-cloud-firestore is required for infer_from_firestore. Install with `pip install infermodel[firestore]`."
        ) from e

    def rows() -> Iterable[Mapping[str, Any]]:
        for doc in query.stream():
            d = doc.to_dict()
            if d is None:
                continue
            yield dict(d)

    return infer(
        rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

