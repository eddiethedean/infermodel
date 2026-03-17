from __future__ import annotations

from typing import Any, Iterable, Mapping
from typing import Optional

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_dataframe(
    df: Any,
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
    chunk_size: Optional[int] = None,
) -> InferResult:
    """
    Infer from a pandas DataFrame (optional dependency).

    If chunk_size is provided, iterate rows in chunks to avoid creating a huge
    list of records at once (still converts each chunk to dict records).
    """
    try:
        import pandas as pd  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "pandas is required for infer_from_dataframe. Install with `pip install infermodel[pandas]`."
        ) from e

    if not isinstance(df, pd.DataFrame):  # type: ignore[attr-defined]
        raise TypeError("df must be a pandas DataFrame")

    if chunk_size is None:
        rows = df.to_dict(orient="records")
        return infer(
            rows,
            config=config,
            model_name=model_name,
            return_model=return_model,
            return_schema=return_schema,
            return_diagnostics=return_diagnostics,
        )

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    def iter_records() -> Iterable[Mapping[str, Any]]:
        n = len(df)
        for start in range(0, n, chunk_size):
            chunk = df.iloc[start : start + chunk_size]
            for rec in chunk.to_dict(orient="records"):
                yield rec

    return infer(
        iter_records(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

