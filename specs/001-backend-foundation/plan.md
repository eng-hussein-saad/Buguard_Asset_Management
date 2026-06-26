# Implementation Plan: Backend Foundation

**Branch**: `[001-backend-foundation]` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-backend-foundation/spec.md`

## Summary

Establish the Phase 1 backend foundation for the Buguard Asset Management API:
a minimal FastAPI application, `/health` endpoint, environment-driven
configuration, async PostgreSQL session setup, Alembic migration foundation,
Docker Compose runtime, README setup notes, and baseline automated quality
checks. The design intentionally excludes tenant/domain models and Phase 2+
behavior while preserving the project structure those later phases will use.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, Pydantic
v2, pydantic-settings, asyncpg, pytest, pytest-asyncio, httpx, ruff, mypy, uv,
Docker Compose

**Storage**: PostgreSQL via async SQLAlchemy sessions; no Phase 1 domain tables
or placeholder schema migrations

**Testing**: pytest, pytest-asyncio, httpx; baseline tests cover `/health` and
configuration failure behavior

**Target Platform**: Linux-compatible API server and Docker Compose local
runtime; local development through `uv`

**Project Type**: Backend web service

**Performance Goals**: `/health` is an application availability check and should
return a successful JSON response within 1 second in local and Docker Compose
runs under normal development conditions.

**Constraints**: Tenant isolation readiness, no committed secrets, sanitized
configuration failures, environment-driven configuration, no Phase 2+ endpoints
or domain models, reproducible local and Docker startup, `ruff` and `mypy`
baseline checks must pass.

**Scale/Scope**: Phase 1 foundation only: app structure, health route,
configuration, database session scaffolding, Alembic readiness, Docker Compose,
README setup notes, `.env.example`, test/lint/type-check commands, and `uv.lock`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. Phase 1 has no tenant-owned resources, client
  `organization_id`, caches, imports, relationships, or AI inputs. The planned
  structure separates dependencies, repositories, services, and database setup
  so Phase 2 can introduce authenticated organization scoping at API and service
  boundaries.
- **Security defaults**: PASS. `DATABASE_URL` is required, loaded from the
  environment, documented in `.env.example`, and missing/malformed values fail
  startup with sanitized errors. No secrets are committed. Auth/token behavior is
  explicitly out of scope for Phase 1.
- **Test coverage**: PASS. Baseline tests are planned for `/health` and required
  configuration behavior. `ruff` and `mypy` are part of the completion gate.
- **Lifecycle integrity**: PASS. Phase 1 does not touch asset ingestion or
  mutation. The model/repository/service directories are created only as
  placeholders for later lifecycle-aware phases.
- **Operational reproducibility**: PASS. Plan covers `uv` commands, Docker
  Compose API/database services, `.env.example`, Alembic no-op verification,
  README setup notes, tests, linting, and type checking.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-foundation/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- openapi.yaml
`-- checklists/
    `-- requirements.md
```

### Source Code (repository root)

```text
app/
|-- __init__.py
|-- main.py
|-- api/
|   |-- __init__.py
|   |-- deps.py
|   `-- routes/
|       |-- __init__.py
|       `-- health.py
|-- core/
|   |-- __init__.py
|   |-- config.py
|   |-- errors.py
|   `-- security.py
|-- db/
|   |-- __init__.py
|   |-- base.py
|   `-- session.py
|-- models/
|   `-- __init__.py
|-- repositories/
|   `-- __init__.py
|-- schemas/
|   `-- __init__.py
`-- services/
    `-- __init__.py

tests/
|-- __init__.py
`-- test_health.py

alembic/
docker-compose.yml
Dockerfile
.env.example
README.md
```

**Structure Decision**: Use the Phase 1 structure from `PLAN.md` exactly. Even
though several packages remain thin in Phase 1, creating the route/config/db/
schema/service/repository boundaries now supports later tenant isolation and
keeps future work aligned with the constitution.

## Phase 0: Research

Research output: [research.md](./research.md)

Resolved decisions:

- Python 3.13 with `uv` for local dependency/runtime workflow.
- FastAPI app factory/entry module with dedicated health router.
- Pydantic Settings for required `DATABASE_URL` and sanitized config failure.
- Async SQLAlchemy session scaffolding with `asyncpg`.
- Alembic configured for future model discovery and no-op verification before
  domain models exist.
- Docker Compose with separate `api` and `db` services.
- Baseline quality gate: `uv run pytest`, `uv run ruff check .`, and
  `uv run mypy app`.

## Phase 1: Design & Contracts

Design outputs:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- **Tenant isolation**: PASS. No tenant-owned data is introduced. The contracts
  expose only `GET /health`.
- **Security defaults**: PASS. Design requires env-based `DATABASE_URL`, no
  fallback secret, sanitized startup failure, and `.env.example` placeholders.
- **Test coverage**: PASS. Quickstart includes test, lint, type-check, health,
  Docker, and Alembic no-op validation commands.
- **Lifecycle integrity**: PASS. No asset lifecycle behavior is implemented or
  modeled in this phase.
- **Operational reproducibility**: PASS. Quickstart documents local and Docker
  paths plus expected outcomes.

## Complexity Tracking

No constitution violations.
