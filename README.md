# Buguard Asset Management Backend

Phase 1 establishes the backend foundation for the Buguard Asset Management
API. The current scope is intentionally small: a FastAPI app, a `/health`
endpoint, required environment configuration, async PostgreSQL session
scaffolding, Alembic readiness, Docker Compose, and baseline quality checks.

Later tenant, authentication, asset, import, relationship, caching, and AI
features are out of scope for this phase.

## Prerequisites

- Python 3.13
- uv
- Docker and Docker Compose

## Environment

Create a local `.env` from `.env.example` and set a development database URL:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/buguard
```

`DATABASE_URL` is required. If it is missing or malformed, the application fails
startup with a sanitized configuration error that does not print the provided
secret value.

## Install

```bash
uv sync
```

## Run Locally

```bash
uv run uvicorn app.main:app --reload
```

Verify the health endpoint in another shell:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Docker Compose

```bash
docker compose up --build
```

If your Docker installation exposes the legacy command, use
`docker-compose up --build` instead.

Default ports:

- API: `localhost:8000`
- PostgreSQL: `localhost:5432`

The `api` service receives:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/buguard
```

Verify the API:

```bash
curl http://localhost:8000/health
```

Verify API-to-PostgreSQL reachability from the API container:

```bash
docker compose exec api uv run python -c "import asyncio; from app.db.session import check_database_reachability; print(asyncio.run(check_database_reachability()))"
```

Expected output:

```text
1
```

## Alembic

Phase 1 creates Alembic configuration only. It does not add domain models or
placeholder migrations.

With `DATABASE_URL` configured:

```bash
uv run alembic current
```

Expected outcome: Alembic connects and exits successfully before any domain
schema migrations exist.

## Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

All three commands are part of the Phase 1 completion gate.

## Contract

The Phase 1 HTTP contract is limited to:

```text
GET /health
```

Response:

```json
{"status":"ok"}
```

The source contract lives at
`specs/001-backend-foundation/contracts/openapi.yaml`.
