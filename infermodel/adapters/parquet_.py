from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping
from typing import Optional, Union

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_parquet(
    path: Union[str, Path],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
    batch_size: int = 10_000,
) -> InferResult:
    """
    Infer from a Parquet file using pyarrow (optional dependency).

    Iterates record batches to keep memory usage bounded.
    """
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "pyarrow is required for infer_from_parquet. Install with `pip install infermodel[parquet]`."
        ) from e

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    def iter_rows() -> Iterable[Mapping[str, Any]]:
        pf = pq.ParquetFile(str(path))
        for batch in pf.iter_batches(batch_size=batch_size):
            # batch.to_pylist() returns list[dict[str, Any]]
            for row in batch.to_pylist():
                yield row

    return infer(
        iter_rows(),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

