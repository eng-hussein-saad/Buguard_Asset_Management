# Buguard Asset Management Backend

The backend provides the FastAPI foundation for Buguard Asset Management,
multi-tenant authentication, tenant-scoped asset CRUD, Phase 4 bulk import
lifecycle handling, and Phase 5 asset relationships with one-hop graph
retrieval. It includes
health checks, async PostgreSQL sessions, Alembic migrations, seeded evaluation
tenants, login, refresh, logout, current-user auth, tenant ownership helpers,
reusable RBAC checks, asset create/list/detail/update/delete endpoints, filters,
sorting, pagination, normalization, idempotent asset import, partial import
summaries, stale reactivation, relationship creation/listing, graph retrieval,
a simple graph visualization, and structured domain errors.

Public registration, public organization creation, membership management,
organization switching, multi-hop graph traversal, caching, and AI analysis are
out of scope for this phase.

## Prerequisites

- Python 3.13
- uv
- Docker and Docker Compose

## Environment

Create a local `.env` from `.env.example` and set a development database URL:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/buguard
JWT_SECRET_KEY=change-me-in-local-dev
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

`DATABASE_URL` is required. If it is missing or malformed, the application fails
startup with a sanitized configuration error that does not print the provided
secret value.

`JWT_SECRET_KEY` must be changed in real deployments and kept local-only. The
default access-token lifetime is 15 minutes and the default refresh-token
lifetime is 7 days.

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

With `DATABASE_URL` configured:

```bash
uv run alembic upgrade head
```

Expected outcome: tables exist for organizations, users, refresh tokens,
assets, and asset relationships.

## Seed Evaluation Data

```bash
uv run python scripts/seed.py
uv run python scripts/seed.py
```

The second run is idempotent. Seeded credentials:

```text
admin@example.com / password123
analyst@example.com / password123
viewer@example.com / password123
other-admin@example.com / password123
```

The first three users belong to the `demo` organization. The fourth user
belongs to the `other` organization.

## Authentication

Log in:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

The response includes `access_token`, `refresh_token`, `token_type: bearer`, and
`expires_in: 900`. Access tokens contain the user id, organization id, role, and
expiry. Refresh tokens are opaque, stored only as hashes, and rotated on every
successful refresh.

Current user:

```bash
curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Refresh:

```bash
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

Logout:

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<replacement_refresh_token>"}'
```

## Assets

Asset operations require a bearer access token. Viewers, analysts, and admins
can list and read assets. Analysts and admins can create, refresh, and update
assets. Only admins can hard delete assets.

Create or refresh a single asset observation:

```bash
curl -s -X POST http://localhost:8000/assets \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"type":"domain","value":" Example.COM ","status":"active","source":"manual","tags":["external"],"metadata":{"owner":"security"}}'
```

Expected outcome: HTTP 201 when a new asset is created, or HTTP 200 when an
existing organization asset with the same type and canonical value is refreshed.
Asset ownership is derived from the authenticated user; `organization_id` in
request bodies is rejected. Existing observations preserve `first_seen`, refresh
`last_seen` from server time, merge tags without duplicates, shallow-merge
metadata with newest values winning conflicts, and reactivate stale assets.
Archived assets remain archived unless `status` is explicitly set to `active`.

List, filter, sort, and paginate assets:

```bash
curl -s "http://localhost:8000/assets?type=domain&status=active&tag=external&source=manual&value_contains=example&sort_by=value&sort_order=asc&page=1&page_size=20" \
  -H "Authorization: Bearer <viewer_access_token>"
```

The response contains `items`, `page`, `page_size`, `total`, `total_pages`,
`has_next`, and `has_previous`.

Read, update, and hard delete:

```bash
curl -s http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <viewer_access_token>"

curl -s -X PATCH http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"stale","tags":["external","review"]}'

curl -i -X DELETE http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <admin_access_token>"
```

Concurrent write conflicts may return HTTP 409 with `DUPLICATE_ASSET`. Missing
or cross-organization asset identifiers return `ASSET_NOT_FOUND`.

## Bulk Import and Lifecycle

Analysts and admins can import observed assets for their own organization:

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"type":"domain","value":"Example.COM","source":"sample-dataset","tags":["external","phase4"],"metadata":{"owner":"security"}},{"type":"subdomain","value":"API.Example.COM","tags":["api"]}]}'
```

Expected outcome: HTTP 200 with `created`, `updated`, `failed`, and `errors`.
Re-running the same payload does not increase the organization asset count;
the existing records are reported as `updated`. Asset ownership is always
derived from the bearer token, and `organization_id` in import records is
rejected as a per-record error.

Mixed valid and invalid records return HTTP 207 with the same summary shape:

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"type":"domain","value":"valid.example.com"},{"type":"domain","value":""},{"type":"unsupported","value":"bad.example.com"}]}'
```

If every record fails record-level validation, the route returns HTTP 422 and
does not create or update assets. Import re-sightings preserve `first_seen`,
refresh `last_seen` from server time, merge tags without duplicates, and
shallow-merge metadata with newest values winning conflicts. Stale assets become
active when imported again; archived assets stay archived unless the import
record explicitly sets `"status":"active"`.

## Relationships and Graphs

Viewers, analysts, and admins can list relationships and retrieve graph data.
Only analysts and admins can create relationships. Relationship ownership is
always derived from the bearer token, and payloads that include
`organization_id` are rejected.

Create a relationship between two assets in the same organization:

```bash
curl -i -X POST http://localhost:8000/relationships \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"source_asset_id":"<source_asset_id>","target_asset_id":"<target_asset_id>","relationship_type":"resolves_to","metadata":{}}'
```

Supported relationship types are `belongs_to`, `resolves_to`, `runs_on`,
`covers`, and `detected_on`. Repeating the same organization, source asset,
target asset, and relationship type returns HTTP 409 with
`DUPLICATE_RELATIONSHIP` and does not create another row.

List relationships for the authenticated organization:

```bash
curl -s http://localhost:8000/relationships \
  -H "Authorization: Bearer <viewer_access_token>"
```

Retrieve the one-hop graph around an asset:

```bash
curl -s http://localhost:8000/assets/<asset_id>/graph \
  -H "Authorization: Bearer <viewer_access_token>"
```

The graph response contains `center`, `nodes`, and `edges`. The center asset is
always present in `nodes`, including isolated assets with no relationships.
Only directly connected organization-owned relationships are returned.

Open the simple evaluator graph view:

```text
http://localhost:8000/assets/<asset_id>/graph/view
```

The view uses the graph endpoint as its data source, labels nodes by asset
value, labels edges by relationship type, and displays structured errors from
the API when graph retrieval fails.

## Tenant Isolation and Roles

Tenant-owned resources derive `organization_id` only from the authenticated
user context. Clients must not supply or override organization ownership.
Cross-organization asset access returns 404, and relationships are allowed only
when both assets belong to the authenticated user's organization.

Role matrix:

| Role | Allowed |
| --- | --- |
| viewer | Read assets, relationships, and graph data |
| analyst | Viewer permissions plus asset create/update, bulk import, stale marking, and relationship creation |
| admin | Analyst permissions plus delete/archive operations |

## Quality Checks

```bash
uv run pytest tests/unit/test_asset_normalization.py
uv run pytest tests/unit/test_asset_relationships.py
uv run pytest tests/contract/test_assets_api.py
uv run pytest tests/integration/test_asset_relationships_graph.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py
uv run pytest tests/integration/test_asset_import_lifecycle.py tests/integration/test_asset_crud.py tests/integration/test_asset_filters.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py
uv run pytest
uv run ruff check .
uv run mypy app
```

The focused asset commands cover asset lifecycle behavior; the full pytest, Ruff, and
mypy commands remain the repository-wide quality gate.

## Contract

The Phase 1 HTTP contract includes:

```text
GET /health
```

Response:

```json
{"status":"ok"}
```

The source contract lives at
`specs/001-backend-foundation/contracts/openapi.yaml`.

The Phase 3 asset API contract lives at
`specs/003-asset-crud/contracts/assets-api.yaml` and covers:

```text
POST /assets
GET /assets
GET /assets/{asset_id}
PATCH /assets/{asset_id}
DELETE /assets/{asset_id}
```

The Phase 4 bulk import contract lives at
`specs/004-bulk-import-lifecycle/contracts/bulk-import-api.yaml` and adds:

```text
POST /assets/import
PATCH /assets/{asset_id} with status=stale lifecycle examples
```

The Phase 5 relationships and graph contract lives at
`specs/005-asset-relationships-graph/contracts/relationships-graph-api.yaml`
and adds:

```text
POST /relationships
GET /relationships
GET /assets/{asset_id}/graph
GET /assets/{asset_id}/graph/view
```
