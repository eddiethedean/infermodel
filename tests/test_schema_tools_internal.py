from __future__ import annotations

from infermodel.schema import ListTypeSpec, ModelTypeSpec, ScalarTypeSpec, UnionTypeSpec
from infermodel.schema_tools import _merge_types, _type_sig


def test_merge_types_union_paths_and_dedup() -> None:
    # a is union, b is scalar
    out = _merge_types(UnionTypeSpec((ScalarTypeSpec("int"),)), ScalarTypeSpec("str"))
    assert isinstance(out, UnionTypeSpec)
    assert len(out.variants) == 2

    # both unions with duplicates
    out2 = _merge_types(
        UnionTypeSpec((ScalarTypeSpec("int"), ScalarTypeSpec("str"))),
        UnionTypeSpec((ScalarTypeSpec("int"),)),
    )
    assert isinstance(out2, UnionTypeSpec)
    assert len(out2.variants) == 2


def test_type_sig_list_and_model_paths() -> None:
    assert _type_sig(ListTypeSpec(ScalarTypeSpec("int")))[0] == "list"
    assert _type_sig(ModelTypeSpec(fields={}))[0] == "model"

