from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_sqlalchemy(
    conn_or_engine: Any,
    selectable: Any,
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer from a SQLAlchemy selectable (Core) using `Result.mappings()` (streaming).

    This adapter is intentionally thin: it executes the selectable and feeds the resulting
    row-mappings into `infer(...)`, so `sample_size` limits how many rows are consumed.

    Requires optional dependency `SQLAlchemy`:
        pip install "infermodel[sqlalchemy]"
    """
    try:
        from sqlalchemy import Engine
        from sqlalchemy.engine import Connection
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "SQLAlchemy is required for infer_from_sqlalchemy. Install with `pip install infermodel[sqlalchemy]`."
        ) from e

    def rows_from_connection(conn: "Connection") -> Iterable[Mapping[str, Any]]:
        result = conn.execute(selectable)
        for row in result.mappings():
            yield dict(row)

    if isinstance(conn_or_engine, Engine):
        with conn_or_engine.connect() as conn:
            return infer(
                rows_from_connection(conn),
                config=config,
                model_name=model_name,
                return_model=return_model,
                return_schema=return_schema,
                return_diagnostics=return_diagnostics,
            )

    # assume Connection-like
    return infer(
        rows_from_connection(conn_or_engine),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

