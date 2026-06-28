# Implementation Plan: Test CI Rate Limits

**Branch**: `[006-test-ci-rate-limits]` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-test-ci-rate-limits/spec.md`

## Summary

Phase 6 hardens the existing FastAPI asset-management backend with
comprehensive regression coverage, GitHub Actions quality checks, rate limits
for login, refresh, and bulk import operations, organization-scoped caching for
asset list and graph reads, and documentation for local and CI verification.
The implementation will extend the current route/schema/service/repository
layout with reusable rate-limit and cache services, preserve authenticated
organization scoping, invalidate cached asset and graph reads after relevant
writes, and keep the later AI analysis endpoint out of scope except for
documenting its intended limit.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2,
asyncpg, pytest, pytest-asyncio, httpx, ruff, mypy, uv, Docker Compose, GitHub
Actions, Redis-compatible cache client

**Storage**: PostgreSQL via async SQLAlchemy sessions; Redis-compatible cache
for rate-limit counters and cached organization-scoped read responses

**Testing**: pytest, pytest-asyncio, httpx, ruff, mypy where project config
supports it

**Target Platform**: Linux-compatible API server, Docker Compose local runtime,
and GitHub Actions hosted Linux runners

**Project Type**: Backend web service

**Performance Goals**: Rate-limit checks must run before expensive login,
refresh, or import work. Cached asset list and one-hop graph reads should avoid
database work on repeated identical organization-scoped requests, while all
cache failures fall back to correct uncached database reads.

**Constraints**: Tenant isolation, no committed secrets, structured errors,
environment-driven configuration, reproducible local and Docker startup,
authenticated organization in every cache key, no client-supplied
`organization_id`, bounded rate-limit windows, cache invalidation after asset,
import, relationship, stale, archive, or delete writes, and no Phase 6 public
registration, organization switching, or AI analysis implementation

**Scale/Scope**: Phase 6 only. Add tests for existing Phase 1-5 behavior, CI
quality checks, login/refresh/import rate limits, cache infrastructure for
asset list and graph reads, cache invalidation/fallback behavior, README and
`.env.example` updates, and verification commands. Later AI analysis remains
future work with only its expected rate limit documented.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. Rate-limit identities are derived from attempted
  username plus client network identity for login, or authenticated user plus
  authenticated organization for refresh and import. Cache identities include
  authenticated organization and all user-visible query inputs. No Phase 6
  payload accepts tenant ownership.
- **Security defaults**: PASS. Login, refresh, and bulk import limits protect
  abuse-prone operations before expensive work continues. Rejections use the
  structured error envelope. Secrets and cache settings remain environment
  driven and documented.
- **Test coverage**: PASS. Phase 6 exists to add automated coverage for health,
  seed/auth, refresh/logout, RBAC, tenant isolation, asset CRUD, import
  lifecycle, relationships, graphs, structured errors, rate limits, caching,
  invalidation, fallback, and CI failure behavior.
- **Lifecycle integrity**: PASS. Import and asset lifecycle behavior is
  preserved and covered by regression tests. Cache invalidation is required
  after writes that change lifecycle-visible asset or relationship state.
- **Operational reproducibility**: PASS. Local uv commands, Docker Compose
  services, GitHub Actions setup, README notes, `.env.example`, linting,
  tests, and optional cache fallback behavior are in scope.
- **Code documentation**: PASS. New or modified Python functions, methods,
  service helpers, repository helpers, cache helpers, and rate-limit helpers
  must include concise docstrings for behavior and side effects.

## Project Structure

### Documentation (this feature)

```text
specs/006-test-ci-rate-limits/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
`-- tasks.md
```

### Source Code (repository root)

```text
app/
|-- api/
|   |-- deps.py
|   `-- routes/
|       |-- assets.py
|       |-- auth.py
|       `-- health.py
|-- core/
|   |-- config.py
|   |-- errors.py
|   `-- security.py
|-- db/
|-- models/
|-- repositories/
|   |-- assets.py
|   |-- auth.py
|   |-- organizations.py
|   |-- relationships.py
|   `-- users.py
|-- schemas/
|   |-- assets.py
|   `-- auth.py
|-- services/
|   |-- auth.py
|   |-- rbac.py
|   `-- tenant_assets.py
`-- main.py

tests/
|-- contract/
|   |-- test_assets_api.py
|   `-- test_auth_api.py
|-- integration/
|   |-- test_asset_crud.py
|   |-- test_asset_filters.py
|   |-- test_asset_import_lifecycle.py
|   |-- test_asset_rbac.py
|   |-- test_asset_relationships_graph.py
|   |-- test_asset_tenant_isolation.py
|   |-- test_auth_flow.py
|   |-- test_rbac.py
|   |-- test_seed.py
|   `-- test_tenant_isolation.py
|-- unit/
|   |-- test_asset_normalization.py
|   |-- test_asset_relationships.py
|   |-- test_security.py
|   `-- test_token_service.py
`-- conftest.py

.github/
`-- workflows/

alembic/
docker-compose.yml
Dockerfile
.env.example
```

**Structure Decision**: Continue the established FastAPI separation. Existing
route modules remain the public API surface: `app/api/routes/auth.py` owns
login, refresh, logout, and current-user behavior; `app/api/routes/assets.py`
owns asset list, import, relationship, and graph behavior. New shared
infrastructure should live under `app/core/` or `app/services/` based on local
patterns: configuration in `app/core/config.py`, structured rate-limit/cache
errors in `app/core/errors.py`, rate-limit decisions in a reusable service,
cache key/build/get/set/invalidate/fallback helpers in a reusable service, and
write-through invalidation calls from `app/services/tenant_assets.py`.
Tests should extend the current contract, integration, and unit layout without
moving existing Phase 1-5 coverage. CI belongs in `.github/workflows/`.

## Phase 0: Research Summary

Research is captured in [research.md](./research.md). All technical unknowns
from the plan template have been resolved for Phase 6. No unresolved
clarification items remain.

## Phase 1: Design Summary

Data design is captured in [data-model.md](./data-model.md). API contracts are
captured in [contracts/test-ci-rate-limits-api.yaml](./contracts/test-ci-rate-limits-api.yaml).
End-to-end validation steps are captured in [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Contracts and data model require authenticated
  organization-derived identities for refresh/import rate limits and cache
  entries. Asset list and graph cache keys include organization scope and all
  response-affecting inputs. Cross-tenant data is never cached under shared
  identities.
- **Security defaults**: PASS. Contracts document 429 structured responses,
  rate-limit identity rules, and cache fallback that serves uncached correct
  data instead of stale or cross-tenant data. Cache configuration is documented
  in `.env.example`.
- **Test coverage**: PASS. Quickstart includes local commands and specific
  scenarios for regression coverage, CI failure, rate-limit thresholds, cache
  isolation, invalidation, and fallback.
- **Lifecycle integrity**: PASS. Data model requires cache invalidation after
  lifecycle-visible writes, including import, stale reactivation, archive or
  delete, relationship create/delete, and asset mutation.
- **Operational reproducibility**: PASS. Validation commands use uv, pytest,
  ruff, optional mypy, Docker Compose, GitHub Actions, README, and
  `.env.example`. Redis/cache unavailability is explicitly non-fatal for reads.
- **Code documentation**: PASS. Implementation tasks must add concise docstrings
  for new/modified rate-limit, cache, service, repository, route, and test
  helper functions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
