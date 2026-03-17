from __future__ import annotations

import typing

from infermodel.schema import ListTypeSpec, ModelTypeSpec, ScalarTypeSpec, TypeSpec, UnionTypeSpec
from infermodel.typing_utils import type_spec_to_annotation


def test_type_spec_to_annotation_scalars() -> None:
    assert type_spec_to_annotation(ScalarTypeSpec("int")) is int
    assert type_spec_to_annotation(ScalarTypeSpec("str")) is str


def test_type_spec_to_annotation_list() -> None:
    ann = type_spec_to_annotation(ListTypeSpec(ScalarTypeSpec("int")))
    assert str(ann).endswith("list[int]") or "list[int]" in str(ann)


def test_type_spec_to_annotation_union_empty_single_multi() -> None:
    assert type_spec_to_annotation(UnionTypeSpec(tuple())) is typing.Any
    ann_single = type_spec_to_annotation(UnionTypeSpec((ScalarTypeSpec("int"),)))
    assert ann_single is int
    ann = type_spec_to_annotation(UnionTypeSpec((ScalarTypeSpec("int"), ScalarTypeSpec("str"))))
    assert "int" in str(ann) and "str" in str(ann)


def test_type_spec_to_annotation_model_placeholder_any() -> None:
    ann = type_spec_to_annotation(ModelTypeSpec(fields={}))
    assert ann is typing.Any


def test_type_spec_to_annotation_unknown_typespec_falls_back_to_any() -> None:
    class Weird(TypeSpec):
        pass

    assert type_spec_to_annotation(Weird()) is typing.Any

