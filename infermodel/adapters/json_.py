from __future__ import annotations

import json
from pathlib import Path
from typing import IO, Any, Iterable, Mapping, Optional, Union

from infermodel.config import InferConfig
from infermodel.infer import InferResult, infer


def infer_from_json(
    path_or_file: Union[str, Path, IO[str]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """Infer from a JSON array of objects (loads the array into memory)."""
    if isinstance(path_or_file, (str, Path)):
        path = Path(path_or_file)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(path_or_file)

    if not isinstance(data, list):
        raise TypeError("JSON input must be an array of objects")
    rows: list[Mapping[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, Mapping):
            raise TypeError(f"JSON array element {i} must be an object")
        rows.append(item)

    return infer(
        rows,
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )


def infer_from_ndjson(
    path_or_file: Union[str, Path, IO[str]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """Infer from NDJSON/JSONL (streaming)."""

    def rows_from_file(f: IO[str]) -> Iterable[Mapping[str, Any]]:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, Mapping):
                raise TypeError(f"NDJSON line {line_no} must be an object")
            yield obj

    if isinstance(path_or_file, (str, Path)):
        path = Path(path_or_file)
        with path.open("r", encoding="utf-8") as f:
            return infer(
                rows_from_file(f),
                config=config,
                model_name=model_name,
                return_model=return_model,
                return_schema=return_schema,
                return_diagnostics=return_diagnostics,
            )

    return infer(
        rows_from_file(path_or_file),
        config=config,
        model_name=model_name,
        return_model=return_model,
        return_schema=return_schema,
        return_diagnostics=return_diagnostics,
    )

