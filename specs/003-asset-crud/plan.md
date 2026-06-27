# Implementation Plan: Asset CRUD

**Branch**: `[003-asset-crud]` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-asset-crud/spec.md`

## Summary

Phase 3 implements the core tenant-scoped asset API: create, list, detail,
update, and hard delete. The implementation will add asset request/response
schemas, an `assets` route module, service-level normalization and RBAC checks,
repository queries for filtering/sorting/pagination, structured domain errors,
OpenAPI response documentation, and tests for CRUD behavior, validation,
duplicate handling, tenant isolation, RBAC, and pagination.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2,
asyncpg, pydantic-settings, pytest, pytest-asyncio, httpx, ruff, mypy, uv,
Docker Compose

**Storage**: PostgreSQL via async SQLAlchemy sessions

**Testing**: pytest, pytest-asyncio, httpx

**Target Platform**: Linux-compatible API server and Docker Compose local
runtime

**Project Type**: Backend web service

**Performance Goals**: Asset list queries must remain organization-scoped and
use bounded pagination. Supported filters and sort fields should map to indexed
or straightforward database expressions, with a maximum `page_size` of 100 to
avoid unbounded reads.

**Constraints**: Tenant isolation, no client-supplied `organization_id`,
structured errors, RBAC at the API/service boundary, value normalization before
storage and duplicate checks, hard delete for Phase 3, environment-driven
configuration, reproducible local and Docker startup

**Scale/Scope**: Phase 3 only. Implement direct asset CRUD, filtering, sorting,
pagination, validation, structured errors, OpenAPI polish, README notes, and
tests. Bulk import, lifecycle re-sighting, relationship APIs, graph retrieval,
rate limiting, caching, and AI analysis remain later phases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. All asset operations derive `organization_id` from
  `get_current_user`; route payloads reject `organization_id`; repository
  methods require organization scope for list, detail, update, and delete.
- **Security defaults**: PASS. Routes use existing authenticated dependencies
  and role permissions. Viewers can read, analysts/admins can create/update,
  and admins alone can hard delete.
- **Test coverage**: PASS. Contract, integration, and unit tests are planned for
  CRUD, filters, sorting, pagination, normalization, duplicate conflicts, RBAC,
  structured errors, and tenant isolation.
- **Lifecycle integrity**: PASS. Phase 3 preserves the existing organization,
  type, and value uniqueness rule and normalizes values before duplicate checks.
  Import merge semantics remain deferred to Phase 4.
- **Operational reproducibility**: PASS. Quickstart covers uv, migrations, seed,
  test, lint, OpenAPI, README, and `.env.example` checks. No new environment
  variable is required.
- **Code documentation**: PASS. New or modified route helpers, services,
  repositories, and schema validators must include concise docstrings.

## Project Structure

### Documentation (this feature)

```text
specs/003-asset-crud/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- assets-api.yaml
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
|   |-- test_asset_rbac.py
|   |-- test_asset_tenant_isolation.py
|   `-- test_auth_flow.py
`-- unit/
    |-- test_asset_normalization.py
    `-- test_security.py
```

**Structure Decision**: Continue the Phase 1/2 separation of FastAPI route,
Pydantic schema, service, repository, and SQLAlchemy model concerns. Asset
routes stay thin and delegate normalization, permissions, duplicate mapping,
not-found behavior, and tenant scoping to `app/services/tenant_assets.py`.
Database filtering, sorting, pagination, uniqueness lookup, update, and hard
delete belong in `app/repositories/assets.py`.

## Phase 0: Research Summary

Research is captured in [research.md](./research.md). All technical unknowns
from the plan template have been resolved for Phase 3. No unresolved
clarification items remain.

## Phase 1: Design Summary

Data design is captured in [data-model.md](./data-model.md). API contracts are
captured in [contracts/assets-api.yaml](./contracts/assets-api.yaml).
End-to-end validation steps are captured in [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Contract payloads omit `organization_id`, data
  model requires tenant scope on every operation, and quickstart validates
  cross-organization list/detail/update/delete behavior.
- **Security defaults**: PASS. RBAC behavior is documented in the data model and
  contract, and forbidden actions use the stable `authorization_failed` error
  code from existing project conventions.
- **Test coverage**: PASS. Quickstart and planned tests cover every Phase 3
  success criterion, including duplicate conflict and normalization behavior.
- **Lifecycle integrity**: PASS. CRUD honors canonical value uniqueness and hard
  delete semantics without implementing Phase 4 import lifecycle rules early.
- **Operational reproducibility**: PASS. Validation commands use existing uv,
  Alembic, seed, Docker, pytest, ruff, and README workflows. No `.env.example`
  change is required unless implementation introduces a new setting.
- **Code documentation**: PASS. Implementation tasks must add concise docstrings
  for new/modified Python functions, methods, services, and repositories.

## Complexity Tracking

No constitution violations are required for this phase.
