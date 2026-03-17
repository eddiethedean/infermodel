from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

from infermodel import InferConfig
from infermodel.adapters import infer_from_sqlalchemy
from infermodel.schema_tools import print_schema


def main() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    md = MetaData()
    users = Table(
        "users",
        md,
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    md.create_all(engine)

    with engine.begin() as conn:
        conn.execute(users.insert(), [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}])

    res = infer_from_sqlalchemy(
        engine,
        select(users),
        model_name="User",
        return_diagnostics=True,
        config=InferConfig(sample_size=0),
    )

    print_schema(res.schema)
    print("diagnostics:", res.diagnostics)

    Model = res.model
    assert Model is not None

    # Demonstrate validation
    print(Model(id=1, name="Alice"))


if __name__ == "__main__":
    main()

