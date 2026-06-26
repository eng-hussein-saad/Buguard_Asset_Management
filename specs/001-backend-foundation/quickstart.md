# Quickstart: Backend Foundation

This guide validates Phase 1 from a clean checkout after implementation.

## Prerequisites

- Python 3.13
- uv
- Docker and Docker Compose

## Environment

Create a local `.env` from `.env.example` and provide a development
`DATABASE_URL` value. The value must not be committed.

Expected documented variable:

```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/buguard
```

## Install Dependencies

```bash
uv sync
```

Expected outcome: dependencies install from `pyproject.toml` and `uv.lock`.

## Run Locally

```bash
uv run uvicorn app.main:app --reload
```

In another shell:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run Tests And Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

Expected outcome: all commands complete successfully.

## Verify Required Configuration

Start the app without `DATABASE_URL`.

Expected outcome: startup fails with an understandable sanitized configuration
error. The error must not print secret values.

## Verify Alembic Foundation

With `DATABASE_URL` configured:

```bash
uv run alembic current
```

Expected outcome: Alembic runs successfully even before domain models or schema
migrations exist.

## Run With Docker Compose

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Expected services:

- `api`
- `db`

## Contract Reference

The Phase 1 HTTP contract is documented in
[`contracts/openapi.yaml`](./contracts/openapi.yaml).
