from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_redisjson(
    client: Any,
    keys: Sequence[str],
    *,
    path: str = ".",
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer from RedisJSON documents using redis-py (optional dependency).

    Fetches JSON docs via `client.json().get(key, path)` and yields mappings.
    """
    try:
        import redis  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "redis is required for infer_from_redisjson. Install with `pip install infermodel[redis]`."
        ) from e

    def rows() -> Iterable[Mapping[str, Any]]:
        json_api = client.json()
        for k in keys:
            doc = json_api.get(k, path)
            if isinstance(doc, Mapping):
                yield dict(doc)
            elif isinstance(doc, list) and len(doc) == 1 and isinstance(doc[0], Mapping):
                # Some RedisJSON versions return [doc] for root path
                yield dict(doc[0])
            else:
                continue

    return infer(
        rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

