# Implementation Plan: Asset Relationships Graph

**Branch**: `[005-asset-relationships-graph]` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-asset-relationships-graph/spec.md`

## Summary

Phase 5 implements tenant-scoped asset relationships, relationship listing,
one-hop asset graph retrieval, and a simple graph visualization. The backend
will extend the existing FastAPI asset module with relationship request and
response schemas, relationship and graph service methods, organization-scoped
repository queries, duplicate relationship handling, and structured errors.
The visualization will consume `GET /assets/{asset_id}/graph` directly and
render the returned center, nodes, and edges without duplicating traversal or
tenant-scoping rules.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, asyncpg,
pytest, pytest-asyncio, httpx, ruff, mypy, uv, Docker Compose

**Storage**: PostgreSQL via async SQLAlchemy sessions

**Testing**: pytest, pytest-asyncio, httpx

**Target Platform**: Linux-compatible API server and Docker Compose local runtime

**Project Type**: Backend web service

**Performance Goals**: Relationship list and graph retrieval must perform
bounded organization-scoped queries suitable for evaluator-scale asset graphs.
Graph retrieval is limited to one hop around the selected asset and must avoid
duplicate nodes or edges in the response.

**Constraints**: Tenant isolation, no committed secrets, structured errors,
environment-driven configuration, reproducible local and Docker startup,
analyst/admin-only relationship creation, viewer-readable relationships and
graphs, no client-supplied `organization_id`, one-hop graph retrieval, and
visualization that consumes the backend graph endpoint

**Scale/Scope**: Phase 5 only. Implement manual relationship creation,
duplicate prevention, organization relationship listing, one-hop asset graph
retrieval, simple graph visualization, tests, README notes, and `.env.example`
checks. Automated relationship inference, multi-hop traversal, caching, rate
limiting, CI expansion, and AI analysis remain outside this phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. Relationship ownership is always derived from
  `current_user.organization_id`; source, target, list, graph, and
  visualization-backed reads are scoped to the authenticated organization.
- **Security defaults**: PASS. Relationship creation requires analyst or admin
  permission. Relationship listing and graph retrieval require authenticated
  viewer, analyst, or admin access. Missing or cross-tenant assets use the
  established asset-not-found behavior.
- **Test coverage**: PASS. Contract, integration, and unit coverage is planned
  for create/list/graph behavior, duplicate prevention, RBAC, invalid
  relationship types, missing assets, cross-tenant blocking, one-hop traversal,
  isolated assets, and visualization route behavior.
- **Lifecycle integrity**: PASS. Phase 5 does not alter asset ingestion,
  deduplication, status transitions, `first_seen`, `last_seen`, tag merge, or
  metadata merge semantics from earlier phases.
- **Operational reproducibility**: PASS. Quickstart covers uv, migrations,
  seed, relationship examples, graph retrieval, visualization smoke checks,
  pytest, ruff, mypy, README, and `.env.example` checks. No new environment
  variable is expected.
- **Code documentation**: PASS. New or modified route helpers, schemas,
  services, repository helpers, and visualization handlers must include concise
  docstrings where they are Python functions or methods.

## Project Structure

### Documentation (this feature)

```text
specs/005-asset-relationships-graph/
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
|-- db/
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

alembic/
docker-compose.yml
Dockerfile
.env.example
```

**Structure Decision**: Continue the established route/schema/service/repository
separation. `app/api/routes/assets.py` owns the public relationship endpoints
under the asset API surface, including `POST /relationships`,
`GET /relationships`, `GET /assets/{asset_id}/graph`, and the simple graph view
route if implemented server-side. `app/schemas/assets.py` owns relationship,
graph node, graph edge, graph response, and visualization error schemas.
`app/services/tenant_assets.py` owns RBAC, source/target availability checks,
duplicate handling, one-hop graph assembly, and structured domain errors.
`app/repositories/relationships.py` owns organization-scoped relationship
persistence, listing, duplicate lookup, and graph adjacency queries. The
existing `AssetRelationship` model and `RelationshipType` enum are reused.

## Phase 0: Research Summary

Research is captured in [research.md](./research.md). All technical unknowns
from the plan template have been resolved for Phase 5. No unresolved
clarification items remain.

## Phase 1: Design Summary

Data design is captured in [data-model.md](./data-model.md). API contracts are
captured in [contracts/relationships-graph-api.yaml](./contracts/relationships-graph-api.yaml).
End-to-end validation steps are captured in [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Contract payloads omit `organization_id`; data
  model requires authenticated organization scope on every relationship lookup,
  mutation, list query, graph query, and visualization-backed request.
- **Security defaults**: PASS. Contract documents bearer authentication and
  structured 401/403/404/409/422-style failures. Relationship creation is
  analyst/admin-only, while viewers keep read access.
- **Test coverage**: PASS. Quickstart and planned tests cover every Phase 5
  success criterion, including cross-tenant relationship blocking, isolated
  graph responses, duplicate conflict behavior, and visualization smoke checks.
- **Lifecycle integrity**: PASS. Relationship work references assets but does
  not mutate asset lifecycle fields or import behavior.
- **Operational reproducibility**: PASS. Validation commands use existing uv,
  Alembic, seed, Docker, pytest, ruff, mypy, README, and `.env.example`
  workflows. No `.env.example` change is required unless implementation
  introduces a new setting.
- **Code documentation**: PASS. Implementation tasks must add concise docstrings
  for new/modified Python functions, methods, services, repositories, and
  validators.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
