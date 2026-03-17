from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_couchdb_view(
    view_result: Any,
    *,
    value_key: str = "value",
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer from CouchDB view results (optional dependency `couchdb`).

    Expects an iterable of row dicts; by default reads each row's `value` field.
    """
    try:
        import couchdb  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "couchdb is required for infer_from_couchdb_view. Install with `pip install infermodel[couchdb]`."
        ) from e

    def rows() -> Iterable[Mapping[str, Any]]:
        for row in view_result:
            if isinstance(row, Mapping):
                val = row.get(value_key)
                if isinstance(val, Mapping):
                    yield dict(val)
            else:
                try:
                    val = row[value_key]
                    if isinstance(val, Mapping):
                        yield dict(val)
                except Exception:
                    continue

    return infer(
        rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

