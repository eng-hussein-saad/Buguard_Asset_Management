# Research: Backend Foundation

## Decision: Use Python 3.13 with uv-managed commands

**Rationale**: The repository and project constitution target a `uv` workflow,
and Phase 1 must be reproducible from a clean checkout. Python 3.13 is already
reflected in the plan template and keeps the project current for the assessment.

**Alternatives considered**:

- Python 3.12: stable, but less aligned with the generated plan template.
- Ad hoc virtualenv/pip workflow: works locally but weakens reproducibility.

## Decision: FastAPI entry point with a dedicated health router

**Rationale**: A minimal `app.main:app` entry point and
`app/api/routes/health.py` keep the health endpoint small while preserving the
route structure needed for later phases.

**Alternatives considered**:

- Define `/health` directly in `main.py`: simpler for one endpoint, but it would
  immediately diverge from the planned route organization.
- Add versioned API routing now: useful later, but unnecessary for the Phase 1
  health contract.

## Decision: Require DATABASE_URL through Pydantic Settings

**Rationale**: The clarified spec requires startup to fail when `DATABASE_URL`
is missing or malformed. Pydantic Settings gives a typed, environment-driven
configuration boundary and supports sanitized validation errors.

**Alternatives considered**:

- Local fallback database URL: convenient, but hides configuration mistakes.
- Allow startup without `DATABASE_URL`: keeps `/health` available, but conflicts
  with the clarified requirement.

## Decision: Async SQLAlchemy session setup with asyncpg

**Rationale**: Later phases will need async API handlers and PostgreSQL access.
Configuring an async engine/session factory in Phase 1 gives future routes a
stable dependency without introducing domain tables early.

**Alternatives considered**:

- Synchronous SQLAlchemy engine: simpler, but less consistent with async FastAPI
  request handling.
- Defer database setup to Phase 2: would violate the Phase 1 foundation scope.

## Decision: Configure Alembic without a placeholder schema migration

**Rationale**: The clarified spec requires Alembic readiness while Phase 1 has
no domain models. A no-op verification command proves migration wiring without
creating fake schema history.

**Alternatives considered**:

- Empty initial migration revision: creates migration history that represents no
  real domain change.
- Defer Alembic to Phase 2: conflicts with Phase 1 deliverables.

## Decision: Docker Compose with separate api and db services

**Rationale**: Separate services mirror production concerns and demonstrate that
the API can consume PostgreSQL through `DATABASE_URL`.

**Alternatives considered**:

- API-only container: misses the database reproducibility requirement.
- Local-only PostgreSQL instructions: relies on hidden machine state.

## Decision: Baseline quality gate includes pytest, ruff, and mypy

**Rationale**: The clarified spec requires Phase 1 to pass tests, linting, and
static type checking. Making all three documented commands part of quickstart
creates a clean baseline for later phases.

**Alternatives considered**:

- Ruff only: catches style issues but not type drift.
- Install mypy but defer passing checks: creates a low-signal quality gate.
