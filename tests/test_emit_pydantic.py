from __future__ import annotations

from pydantic import ConfigDict

from infermodel.emit_pydantic import model_from_schema


def test_alias_by_path_applies() -> None:
    schema = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "user": {
                "type": {
                    "type": "model",
                    "fields": {"first_name": {"type": "str", "required": True, "nullable": False}},
                },
                "required": True,
                "nullable": False,
            }
        },
    }
    Model = model_from_schema(schema, model_name="M", alias_by_path={"user.first_name": "firstName"})
    inst = Model(user={"firstName": "A"})
    assert inst.user.first_name == "A"


def test_model_config_only_applies_at_root() -> None:
    schema = {
        "schema_version": 1,
        "type": "model",
        "fields": {
            "user": {
                "type": {
                    "type": "model",
                    "fields": {"name": {"type": "str", "required": True, "nullable": False}},
                },
                "required": True,
                "nullable": False,
            }
        },
    }
    cfg = ConfigDict(extra="forbid")
    Model = model_from_schema(schema, model_name="Root", model_config=cfg)
    # Root forbids extra
    try:
        Model(user={"name": "x"}, extra_field=1)  # type: ignore[call-arg]
        assert False, "expected extra to be forbidden"
    except Exception:
        pass
    # Nested uses default extra behavior (should ignore/allow depending on pydantic default).
    inst = Model(user={"name": "x", "extra_nested": 1})
    assert inst.user.name == "x"


def test_model_name_sanitization() -> None:
    schema = {"schema_version": 1, "type": "model", "fields": {"x": {"type": "int", "required": True, "nullable": False}}}
    Model = model_from_schema(schema, model_name="Weird Name!!!")
    assert Model.__name__.startswith("Weird_Name")

