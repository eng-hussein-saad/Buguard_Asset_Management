# Implementation Plan: Bulk Import Lifecycle

**Branch**: `[004-bulk-import-lifecycle]` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-bulk-import-lifecycle/spec.md`

## Summary

Phase 4 implements tenant-scoped, lifecycle-aware asset ingestion through
`POST /assets/import` and stale status updates through the existing
`PATCH /assets/{asset_id}` route. The implementation will add import request
and response schemas, an import route on the assets router, service logic for
per-record validation and idempotent create/update behavior, repository helpers
for organization-scoped lookup by type and canonical value, predictable tag and
metadata merging, partial failure summaries, and tests for deduplication,
lifecycle transitions, malformed records, RBAC, server-time timestamps, and
tenant isolation.

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

**Performance Goals**: Import processing must perform bounded per-request work,
return a readable summary, avoid unbounded response payloads, and keep all
deduplication lookups scoped by `organization_id`, `type`, and canonical
`value`. The implementation should support evaluator-scale sample datasets
without duplicate writes or cross-tenant queries.

**Constraints**: Tenant isolation, no client-supplied `organization_id`, analyst
or admin permission for import and stale updates, structured errors for
request-level failures, stable per-record import error shape, server-owned
lifecycle timestamps, canonical value matching, shallow metadata merge,
deduplicated tag merge, environment-driven configuration, reproducible local
and Docker startup

**Scale/Scope**: Phase 4 only. Implement bulk import, deduplication, lifecycle
refresh, malformed-record summaries, status reactivation rules, stale marking
through `PATCH /assets/{asset_id}`, README notes if evaluator workflows change,
and tests. Relationship APIs, graph retrieval, rate limiting, caching, CI
expansion, and AI analysis remain later phases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. Import ownership is always derived from
  `get_current_user`; import payloads forbid `organization_id`; deduplication,
  creates, updates, stale marking, and tenant-isolation tests are scoped to
  `current_user.organization_id`.
- **Security defaults**: PASS. Import and stale mutation require analyst/admin
  permissions, viewer attempts are rejected with the established structured
  authorization error, and cross-organization asset references continue to use
  the Phase 3 asset-not-found behavior.
- **Test coverage**: PASS. Contract, integration, and unit tests are planned for
  idempotent import, duplicate records within one batch, malformed records,
  partial and all-record failure statuses, tag and metadata merges, stale
  reactivation, archived asset handling, server-time timestamps, RBAC, and
  tenant isolation.
- **Lifecycle integrity**: PASS. The plan preserves first-seen on re-sighting,
  updates last-seen from server processing time, merges tags without
  duplicates, shallow-merges metadata with newest value winning conflicts,
  reactivates stale assets, and reactivates archived assets only when
  `status=active` is explicit.
- **Operational reproducibility**: PASS. Quickstart covers uv, migrations, seed,
  import examples, test, lint, README, and `.env.example` checks. No new
  environment variable is expected for Phase 4.
- **Code documentation**: PASS. New or modified route helpers, schema
  validators, services, repository helpers, and merge functions must include
  concise docstrings.

## Project Structure

### Documentation (this feature)

```text
specs/004-bulk-import-lifecycle/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- bulk-import-api.yaml
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

**Structure Decision**: Continue the established route/schema/service/repository
separation from Phase 3. The assets router owns the public
`POST /assets/import` endpoint and the existing `PATCH /assets/{asset_id}`
stale update. `app/schemas/assets.py` owns import request/summary schemas.
`app/services/tenant_assets.py` owns per-record validation, RBAC, canonical
value normalization, status transition rules, tag and metadata merge behavior,
and response status classification. `app/repositories/assets.py` owns
organization-scoped lookups and persistence helpers.

## Phase 0: Research Summary

Research is captured in [research.md](./research.md). All technical unknowns
from the plan template have been resolved for Phase 4. No unresolved
clarification items remain.

## Phase 1: Design Summary

Data design is captured in [data-model.md](./data-model.md). API contracts are
captured in [contracts/bulk-import-api.yaml](./contracts/bulk-import-api.yaml).
End-to-end validation steps are captured in [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Contract payloads omit `organization_id`; data
  model requires authenticated organization scope on every import lookup and
  mutation; quickstart validates same-value imports across two organizations.
- **Security defaults**: PASS. Contract documents bearer authentication and
  401/403 structured errors. Import and stale mutation use existing role
  permissions and avoid leaking cross-organization asset existence.
- **Test coverage**: PASS. Quickstart and planned tests cover every Phase 4
  success criterion, including partial failure HTTP 207 and all-record failure
  HTTP 422 behavior.
- **Lifecycle integrity**: PASS. Data model and contract document server-owned
  timestamps, first-seen preservation, last-seen refresh, tag/metadata merge,
  stale reactivation, and archived reactivation only on explicit `active`.
- **Operational reproducibility**: PASS. Validation commands use existing uv,
  Alembic, seed, Docker, pytest, ruff, and README workflows. No `.env.example`
  change is required unless implementation introduces a new setting.
- **Code documentation**: PASS. Implementation tasks must add concise docstrings
  for new/modified Python functions, methods, services, repositories, and
  validators.

## Complexity Tracking

No constitution violations are required for this phase.
