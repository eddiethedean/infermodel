"""Primary public API: infer(...) returning a rich result object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping, Optional, Tuple

from pydantic import ValidationError

import infermodel._infermodel as _infermodel
from infermodel.config import InferConfig
from infermodel.emit_pydantic import model_from_schema
from infermodel.schema import SchemaModel, schema_from_dict


@dataclass(frozen=True)
class InferResult:
    """Result of inference: typed schema, dict schema, optional model, optional diagnostics."""

    schema: Optional[SchemaModel]
    schema_dict: Optional[dict[str, Any]]
    model: Optional[type]
    diagnostics: Optional[dict[str, Any]]


def infer(
    data: Iterable[Mapping[str, Any]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_model: bool = True,
    return_schema: bool = True,
    return_diagnostics: bool = False,
) -> InferResult:
    """
    Infer a schema (and optionally a Pydantic model) from an iterable of mappings.

    This is the primary entrypoint for infermodel.
    """
    _config = config if config is not None else InferConfig()

    if return_diagnostics:
        out: dict[str, Any] = _infermodel.infer_schema_with_diagnostics(
            data,
            infer_string_numbers=_config.infer_string_numbers,
            infer_string_literals=_config.infer_string_literals,
            incompatible_scalar_policy=_config.incompatible_scalar_policy,
            heterogeneous_list_policy=_config.heterogeneous_list_policy,
            dict_mixed_policy=_config.dict_mixed_policy,
            string_date_policy=_config.string_date_policy,
            numeric_promotion=_config.numeric_promotion,
            missing_key_policy=_config.missing_key_policy,
            null_policy=_config.null_policy,
            sample_size=_config.sample_size,
        )
        raw_schema = out["schema"]
        diagnostics = out.get("diagnostics")
    else:
        raw_schema = _infermodel.infer_schema(
            data,
            infer_string_numbers=_config.infer_string_numbers,
            infer_string_literals=_config.infer_string_literals,
            incompatible_scalar_policy=_config.incompatible_scalar_policy,
            heterogeneous_list_policy=_config.heterogeneous_list_policy,
            dict_mixed_policy=_config.dict_mixed_policy,
            string_date_policy=_config.string_date_policy,
            numeric_promotion=_config.numeric_promotion,
            missing_key_policy=_config.missing_key_policy,
            null_policy=_config.null_policy,
            sample_size=_config.sample_size,
        )
        diagnostics = None

    # Enforce schema v1 wrapper even if Rust doesn't emit it yet.
    schema_dict = dict(raw_schema)
    schema_dict.setdefault("schema_version", 1)

    schema_obj = schema_from_dict(schema_dict)

    model = model_from_schema(schema_obj, model_name=model_name) if return_model else None

    return InferResult(
        schema=schema_obj if return_schema else None,
        schema_dict=schema_obj.to_dict() if return_schema else None,
        model=model,
        diagnostics=diagnostics,
    )


def infer_iter(
    data: Iterable[Mapping[str, Any]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_diagnostics: bool = False,
) -> Tuple[InferResult, Iterator[Any]]:
    """
    Infer a model once, then yield validated Pydantic instances for each row.

    Works well for generators: we buffer the sampled rows used for inference, then
    yield instances for buffered rows followed by the remainder of the iterable.

    Note: if config.sample_size == 0, we must consume the full iterable to infer
    the schema before yielding any instances.
    """
    _config = config if config is not None else InferConfig()

    it = iter(data)
    if _config.sample_size == 0:
        buffered = list(it)
        res = infer(
            buffered,
            config=_config,
            model_name=model_name,
            return_model=True,
            return_schema=True,
            return_diagnostics=return_diagnostics,
        )
        Model = res.model
        assert Model is not None

        def gen_all() -> Iterator[Any]:
            for row in buffered:
                yield Model(**row)

        return res, gen_all()

    n = _config.sample_size
    buffered = []
    for _ in range(n):
        try:
            buffered.append(next(it))
        except StopIteration:
            break

    res = infer(
        buffered,
        config=_config,
        model_name=model_name,
        return_model=True,
        return_schema=True,
        return_diagnostics=return_diagnostics,
    )
    Model = res.model
    assert Model is not None

    def gen() -> Iterator[Any]:
        for row in buffered:
            yield Model(**row)
        for row in it:
            yield Model(**row)

    return res, gen()


def infer_iter_rows(
    data: Iterable[Mapping[str, Any]],
    *,
    config: Optional[InferConfig] = None,
    model_name: str = "InferredModel",
    return_diagnostics: bool = False,
) -> Tuple[InferResult, Iterator[Tuple[Mapping[str, Any], Optional[Any], Optional[Exception]]]]:
    """
    Like infer_iter(...), but yields `(row, model_or_none, error_or_none)` for every row.

    Invalid rows do not stop iteration; they yield `(row, None, ValidationError)`.
    """
    _config = config if config is not None else InferConfig()
    it = iter(data)

    if _config.sample_size == 0:
        buffered = list(it)
        res = infer(
            buffered,
            config=_config,
            model_name=model_name,
            return_model=True,
            return_schema=True,
            return_diagnostics=return_diagnostics,
        )
        Model = res.model
        assert Model is not None

        def gen_all() -> Iterator[Tuple[Mapping[str, Any], Optional[Any], Optional[Exception]]]:
            for row in buffered:
                try:
                    yield row, Model(**row), None
                except ValidationError as e:  # pragma: no cover
                    yield row, None, e

        return res, gen_all()

    buffered = []
    for _ in range(_config.sample_size):
        try:
            buffered.append(next(it))
        except StopIteration:
            break

    res = infer(
        buffered,
        config=_config,
        model_name=model_name,
        return_model=True,
        return_schema=True,
        return_diagnostics=return_diagnostics,
    )
    Model = res.model
    assert Model is not None

    def gen() -> Iterator[Tuple[Mapping[str, Any], Optional[Any], Optional[Exception]]]:
        for row in buffered:
            try:
                yield row, Model(**row), None
            except ValidationError as e:
                yield row, None, e
        for row in it:
            try:
                yield row, Model(**row), None
            except ValidationError as e:
                yield row, None, e

    return res, gen()

