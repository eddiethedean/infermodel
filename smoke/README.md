# Smoke tests (local-only)

These are **local-only** smoke tests that hit real backends. They are **not** run in CI.

They are intended to quickly validate that adapter inputs, streaming, and model emission work end-to-end in a realistic environment.

## Setup

From the repo root:

```bash
source .venv/bin/activate
pip install -e ".[adapters]"
```

## SQLAlchemy + SQLite (no Docker)

```bash
python smoke/sqlalchemy_sqlite.py
```

## MongoDB + RedisJSON (Docker)

Start services:

```bash
docker compose -f smoke/docker-compose.yml up -d
```

Run smokes:

```bash
python smoke/mongodb.py
python smoke/redisjson.py
```

Stop services:

```bash
docker compose -f smoke/docker-compose.yml down
```

