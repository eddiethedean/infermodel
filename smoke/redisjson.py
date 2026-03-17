from __future__ import annotations

import redis

from infermodel import InferConfig
from infermodel.adapters import infer_from_redisjson
from infermodel.schema_tools import print_schema


def main() -> None:
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    json_api = client.json()

    # Seed a few docs
    json_api.set("user:1", ".", {"id": 1, "name": "Alice", "active": True})
    json_api.set("user:2", ".", {"id": 2, "name": None, "active": False})
    json_api.set("user:3", ".", {"id": 3, "active": True})

    res = infer_from_redisjson(
        client,
        ["user:1", "user:2", "user:3"],
        model_name="RedisUser",
        return_diagnostics=True,
        config=InferConfig(sample_size=0),
    )

    print_schema(res.schema)
    print("diagnostics:", res.diagnostics)

    Model = res.model
    assert Model is not None
    print(Model(id=1, name="Alice", active=True))


if __name__ == "__main__":
    main()

