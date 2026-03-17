from __future__ import annotations

import csv
from pathlib import Path
from typing import IO, Any, Mapping, Optional, Union

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_csv(
    path_or_file: Union[str, Path, IO[str]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
    dialect: Union[str, csv.Dialect] = "excel",
    **csv_reader_kwargs: Any,
) -> InferResult:
    """
    Infer from CSV using stdlib csv.DictReader (streaming).

    `csv_reader_kwargs` are passed to csv.DictReader (e.g. delimiter=..., fieldnames=...).
    """
    if isinstance(path_or_file, (str, Path)):
        path = Path(path_or_file)
        with path.open("r", encoding=csv_reader_kwargs.pop("encoding", "utf-8"), newline="") as f:
            reader = csv.DictReader(f, dialect=dialect, **csv_reader_kwargs)
            return infer(
                reader,  # type: ignore[arg-type]
                config=config,
                model_name=model_name,
                return_model=return_model,
                return_schema=return_schema,
                return_diagnostics=return_diagnostics,
            )

    reader = csv.DictReader(path_or_file, dialect=dialect, **csv_reader_kwargs)
    return infer(
        reader,  # type: ignore[arg-type]
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

