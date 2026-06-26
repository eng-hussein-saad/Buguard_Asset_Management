# Implementation Plan: Multi-Tenant Auth

**Branch**: `[002-multi-tenant-auth]` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-multi-tenant-auth/spec.md`

## Summary

Phase 2 establishes the security and tenant-ownership foundation for the asset
management backend. The implementation will add organization, user, refresh
token, asset, and asset relationship persistence; seed two evaluation tenants
with four known users; expose only login, refresh, logout, and current-user auth
endpoints; and provide reusable FastAPI dependencies for authenticated tenant
context and viewer/analyst/admin RBAC. Public registration, organization
creation, memberships, and organization switching remain out of scope.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2,
asyncpg, pydantic-settings, pytest, pytest-asyncio, httpx, ruff, mypy, uv,
Docker Compose. Add `python-jose[cryptography]` for JWT handling and
`passlib[bcrypt]` for password hashing.

**Storage**: PostgreSQL via async SQLAlchemy sessions

**Testing**: pytest, pytest-asyncio, httpx

**Target Platform**: Linux-compatible API server and Docker Compose local
runtime

**Project Type**: Backend web service

**Performance Goals**: Auth dependencies and tenant-scoped repository queries
must use indexed lookup paths for email, organization ownership, token owner,
asset lookup, and relationship lookup. Seed workflow must be idempotent on
repeated local runs.

**Constraints**: Tenant isolation, no committed secrets, structured errors,
environment-driven configuration, hashed passwords, hashed refresh tokens,
short-lived access tokens, refresh-token rotation, reproducible local and Docker
startup

**Scale/Scope**: Phase 2 only. Implement foundational data model, seeded users,
auth/session endpoints, tenant context, RBAC helpers, tenant-aware asset and
relationship ownership checks needed to prove isolation. Full asset CRUD,
bulk import, graph retrieval, rate limiting, caching, and AI analysis remain
later phases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. The plan derives tenant ownership from
  authenticated context only, rejects client-supplied organization ownership,
  scopes asset and relationship queries by organization, and standardizes
  cross-tenant asset references as 404 Not Found.
- **Security defaults**: PASS. Passwords and refresh tokens are hashed, access
  tokens include user id, organization id, role, and expiry, token lifetimes are
  environment-driven with safe defaults, and RBAC is enforced through reusable
  dependencies.
- **Test coverage**: PASS. Tests are planned for seed idempotency, login,
  access-token claims, current user, refresh rotation, logout revocation, invalid
  tokens, RBAC decisions, and tenant isolation.
- **Lifecycle integrity**: PASS. Phase 2 only defines asset and relationship
  lifecycle fields and uniqueness constraints. Import merge semantics are
  deferred to Phase 4.
- **Operational reproducibility**: PASS. Alembic migrations, seed instructions,
  `.env.example`, README auth notes, and uv/pytest/ruff validation commands are
  included.

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-tenant-auth/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- auth-api.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
app/
|-- api/
|   |-- deps.py
|   `-- routes/
|       |-- auth.py
|       `-- health.py
|-- core/
|   |-- config.py
|   |-- errors.py
|   `-- security.py
|-- db/
|   |-- base.py
|   `-- session.py
|-- models/
|   |-- asset.py
|   |-- organization.py
|   |-- refresh_token.py
|   `-- user.py
|-- repositories/
|   |-- assets.py
|   |-- auth.py
|   |-- organizations.py
|   |-- relationships.py
|   `-- users.py
|-- schemas/
|   `-- auth.py
|-- services/
|   |-- auth.py
|   |-- rbac.py
|   `-- tenant_assets.py
`-- main.py

scripts/
`-- seed.py

tests/
|-- contract/
|   `-- test_auth_api.py
|-- integration/
|   |-- test_auth_flow.py
|   |-- test_rbac.py
|   |-- test_seed.py
|   `-- test_tenant_isolation.py
`-- unit/
    |-- test_security.py
    `-- test_token_service.py

alembic/
docker-compose.yml
Dockerfile
.env.example
```

**Structure Decision**: Keep the Phase 1 FastAPI separation of routes,
schemas, services, repositories, models, configuration, and database setup.
Auth route handlers stay thin and delegate credential validation, token
issuance, refresh rotation, and logout revocation to services. Tenant-scoped
database access belongs in repositories so later asset CRUD and relationship
features reuse the same organization filters.

## Phase 0: Research Summary

Research is captured in [research.md](./research.md). All technical unknowns
from the template have been resolved for Phase 2. No unresolved clarification
items remain.

## Phase 1: Design Summary

Data design is captured in [data-model.md](./data-model.md). API contracts are
captured in [contracts/auth-api.yaml](./contracts/auth-api.yaml). End-to-end
validation steps are captured in [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Data model requires organization ownership on
  assets and relationships, unique constraints are organization-scoped, and
  contract payloads do not accept organization ownership from clients.
- **Security defaults**: PASS. Contract and data model require hashed secrets,
  refresh-token rotation, token expiry defaults, revocation, and claim
  validation.
- **Test coverage**: PASS. Quickstart and planned tests cover the acceptance
  criteria and security edge cases for Phase 2.
- **Lifecycle integrity**: PASS. Asset status and timestamp fields are present,
  while import lifecycle behavior is explicitly deferred.
- **Operational reproducibility**: PASS. Quickstart includes migration, seed,
  test, lint, README, and `.env.example` checks.

## Complexity Tracking

No constitution violations are required for this phase.
