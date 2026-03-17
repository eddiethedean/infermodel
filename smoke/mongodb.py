from __future__ import annotations

from pymongo import MongoClient

from infermodel import InferConfig
from infermodel.adapters import infer_from_mongodb
from infermodel.schema_tools import print_schema


def main() -> None:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
    db = client["infermodel_smoke"]
    coll = db["users"]
    coll.drop()
    coll.insert_many(
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": None},
            {"id": 3},
        ]
    )

    res = infer_from_mongodb(
        coll,
        model_name="MongoUser",
        return_diagnostics=True,
        config=InferConfig(sample_size=0),
    )

    print_schema(res.schema)
    print("diagnostics:", res.diagnostics)

    Model = res.model
    assert Model is not None
    print(Model(id=1, name="Alice"))


if __name__ == "__main__":
    main()

