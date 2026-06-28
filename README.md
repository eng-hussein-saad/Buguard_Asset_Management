# Buguard Asset Management Backend

The backend provides the FastAPI foundation for Buguard Asset Management,
multi-tenant authentication, tenant-scoped asset CRUD, Phase 4 bulk import
lifecycle handling, and Phase 5 asset relationships with one-hop graph
retrieval, Phase 6 rate limits, organization-scoped cached reads, and CI
quality checks, plus a Phase 7 LangChain-powered grounded analysis report,
shared certificate lifecycle classification, and sample-shaped import
relationships. It includes
health checks, async PostgreSQL sessions, Alembic migrations, seeded evaluation
tenants, login, refresh, logout, current-user auth, tenant ownership helpers,
reusable RBAC checks, asset create/list/detail/update/delete endpoints, filters,
sorting, pagination, normalization, idempotent asset import, partial import
summaries, stale reactivation, relationship creation/listing, graph retrieval,
a simple graph visualization, structured domain errors, fixed-window rate
limits, LangChain-backed `/analysis/report` responses, parent/covers import
relationships, and graceful cache and analysis-provider fallback.

Public registration, public organization creation, membership management,
organization switching, multi-organization membership, live scanning,
cross-organization reports, and multi-hop graph traversal are out of scope.

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
CACHE_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_REFRESH_ATTEMPTS=10
RATE_LIMIT_BULK_IMPORT_ATTEMPTS=10
RATE_LIMIT_AI_ANALYSIS_ATTEMPTS=5
ANALYSIS_PROVIDER=
ANALYSIS_MODEL=
ANALYSIS_API_KEY=
ANALYSIS_BASE_URL=
ANALYSIS_HTTP_REFERER=
ANALYSIS_APP_TITLE=
ANALYSIS_TIMEOUT_SECONDS=30
ANALYSIS_EVIDENCE_LIMIT=50
```

`DATABASE_URL` is required. If it is missing or malformed, the application fails
startup with a sanitized configuration error that does not print the provided
secret value.

`JWT_SECRET_KEY` must be changed in real deployments and kept local-only. The
default access-token lifetime is 15 minutes and the default refresh-token
lifetime is 7 days.

`CACHE_URL` points to the optional Redis-compatible cache. If it is absent or
unreachable, asset list and graph reads use graceful fallback and return correct
database-backed results. `CACHE_TTL_SECONDS` controls cached read lifetime.

`RATE_LIMIT_WINDOW_SECONDS`, `RATE_LIMIT_LOGIN_ATTEMPTS`,
`RATE_LIMIT_REFRESH_ATTEMPTS`, `RATE_LIMIT_BULK_IMPORT_ATTEMPTS`, and
`RATE_LIMIT_AI_ANALYSIS_ATTEMPTS` define the fixed-window policy.

`ANALYSIS_PROVIDER`, `ANALYSIS_MODEL`, `ANALYSIS_API_KEY`, and
`ANALYSIS_BASE_URL` configure the LangChain analysis provider. For OpenRouter's
free NVIDIA Nemotron 3 Ultra model, use:

```bash
ANALYSIS_PROVIDER=openrouter
ANALYSIS_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
ANALYSIS_API_KEY=<your_openrouter_key>
ANALYSIS_BASE_URL=https://openrouter.ai/api/v1
ANALYSIS_HTTP_REFERER=http://localhost:8000
ANALYSIS_APP_TITLE=Buguard Asset Management
```

`ANALYSIS_HTTP_REFERER` and `ANALYSIS_APP_TITLE` are optional OpenRouter
attribution headers. If the provider name or API key is absent, the API still
starts and core asset workflows keep working; `/analysis/report` returns a
structured `analysis_unavailable` response. `ANALYSIS_TIMEOUT_SECONDS` and
`ANALYSIS_EVIDENCE_LIMIT` document the bounded provider input policy.

## Install

```bash
uv sync --all-groups
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
- Redis-compatible cache: `localhost:6379`

The `api` service receives:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/buguard
CACHE_URL=redis://redis:6379/0
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

Login is limited to 5 login attempts per 60 seconds for the same attempted
email and client network identity. Refresh is limited to 10 refresh attempts
per 60 seconds for the authenticated refresh-token user and organization.
Requests over the threshold return HTTP 429 with the structured
`rate_limited` error code and `retry_after_seconds` metadata.

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

Bulk import is limited to 10 bulk import attempts per 60 seconds for the
authenticated user and organization. Viewer users remain forbidden by RBAC
instead of consuming import rate-limit allowance.

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

## Organization-Scoped Cache

`GET /assets` and `GET /assets/{asset_id}/graph` use an organization-scoped
cache when `CACHE_URL` is configured. Asset-list cache keys include the
authenticated organization plus type, status, tag, source, value filter, sort
field, sort order, page, and page size. Graph cache keys include the
authenticated organization and center asset id.

The cache is invalidated after asset create or refresh, asset update, asset
delete or archive, bulk import, relationship creation, and stale marking.
Cached payloads are never shared across organizations. If the cache service is
unavailable or returns invalid data, the API falls back to database reads and
continues returning tenant-scoped results.

Cached read endpoints include an `X-Cache` response header. `X-Cache: MISS`
means the request was served from the database and then cached. `X-Cache: HIT`
means the response was served from cache. `X-Cache: BYPASS` means the
configured cache service was unavailable, so the API skipped cache usage and
served the database result.

## Manual Test Cases

Run the local stack before testing:

```bash
uv sync --all-groups
docker compose up -d db redis
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload
```

Use this helper login sequence to capture tokens for later requests:

```bash
ADMIN_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}')
ADMIN_ACCESS_TOKEN=$(echo "$ADMIN_LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
ADMIN_REFRESH_TOKEN=$(echo "$ADMIN_LOGIN" | sed -n 's/.*"refresh_token":"\([^"]*\)".*/\1/p')

ANALYST_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"password123"}')
ANALYST_ACCESS_TOKEN=$(echo "$ANALYST_LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

VIEWER_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@example.com","password":"password123"}')
VIEWER_ACCESS_TOKEN=$(echo "$VIEWER_LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
```

### Health Check

Request:

```bash
curl -i http://localhost:8000/health
```

Expected result: HTTP 200 with body `{"status":"ok"}`.

### Login Success

Request body:

```json
{"email":"admin@example.com","password":"password123"}
```

Request:

```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

Expected result: HTTP 200 with `access_token`, `refresh_token`, `token_type`,
and `expires_in`.

### Login Rate Limit

Request body:

```json
{"email":"rate-limit@example.com","password":"wrong-password"}
```

Request:

```bash
for i in {1..6}; do
  curl -i -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"rate-limit@example.com","password":"wrong-password"}'
done
```

Expected result: attempts below the threshold return HTTP 401 for invalid
credentials; the 6th attempt within 60 seconds returns HTTP 429 with
`error.code` set to `rate_limited` and `details.operation` set to `login`.

### Refresh Token Rotation

Request body:

```json
{"refresh_token":"<current_refresh_token>"}
```

Request:

```bash
REFRESH_RESPONSE=$(curl -s -i -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$ADMIN_REFRESH_TOKEN\"}")
echo "$REFRESH_RESPONSE"
ADMIN_REFRESH_TOKEN=$(echo "$REFRESH_RESPONSE" | sed -n 's/.*"refresh_token":"\([^"]*\)".*/\1/p')
```

Expected result: HTTP 200 with a new `access_token` and a new `refresh_token`.
The submitted refresh token is revoked and cannot be reused.

### Refresh Rate Limit

Request body shape:

```json
{"refresh_token":"<latest_refresh_token>"}
```

Request:

```bash
TOKEN="$ADMIN_REFRESH_TOKEN"
for i in {1..11}; do
  RESPONSE=$(curl -s -i -X POST http://localhost:8000/auth/refresh \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\":\"$TOKEN\"}")
  echo "$RESPONSE"
  NEW_TOKEN=$(echo "$RESPONSE" | sed -n 's/.*"refresh_token":"\([^"]*\)".*/\1/p')
  if [ -n "$NEW_TOKEN" ]; then
    TOKEN="$NEW_TOKEN"
  fi
done
```

Expected result: the first 10 valid refresh attempts within 60 seconds return
HTTP 200 and rotate the token; the 11th returns HTTP 429 with `error.code` set
to `rate_limited` and `details.operation` set to `refresh`.

### Current User

Request:

```bash
curl -i http://localhost:8000/auth/me \
  -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN"
```

Expected result: HTTP 200 with the authenticated user's id, email,
organization id, role, and active status.

### Logout

Request body:

```json
{"refresh_token":"<latest_refresh_token>"}
```

Request:

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$TOKEN\"}"
```

Expected result: HTTP 204. Reusing that refresh token returns HTTP 401.

### Create Or Refresh Asset

Request body:

```json
{
  "type": "domain",
  "value": "Manual-Test.Example.com",
  "status": "active",
  "source": "manual-test",
  "tags": ["manual", "phase6"],
  "metadata": {"owner": "security"}
}
```

Request:

```bash
ASSET_CREATE=$(curl -s -X POST http://localhost:8000/assets \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"domain","value":"Manual-Test.Example.com","status":"active","source":"manual-test","tags":["manual","phase6"],"metadata":{"owner":"security"}}')
ASSET_ID=$(echo "$ASSET_CREATE" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "$ASSET_CREATE"
```

Expected result: HTTP 201 for a new asset, or HTTP 200 if the same
organization/type/canonical value already exists. The response value is
canonicalized to lowercase for domains.

### List Assets With Filters

Request:

```bash
curl -i "http://localhost:8000/assets?type=domain&status=active&tag=manual&source=manual-test&value_contains=manual-test&sort_by=value&sort_order=asc&page=1&page_size=20" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"
```

Expected result: HTTP 200 with `items`, `page`, `page_size`, `total`,
`total_pages`, `has_next`, and `has_previous`. For cacheable list reads, the
first identical request returns `X-Cache: MISS`; repeating the same request
returns `X-Cache: HIT`.

### Update Asset And Cache Invalidation

Request body:

```json
{"status":"stale","tags":["manual","phase6","reviewed"]}
```

Request:

```bash
curl -i -X PATCH "http://localhost:8000/assets/$ASSET_ID" \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"stale","tags":["manual","phase6","reviewed"]}'

curl -i "http://localhost:8000/assets?status=stale&tag=reviewed" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"
```

Expected result: the patch returns HTTP 200, and the repeated list read reflects
the updated status/tags instead of serving a stale cached list.

### Bulk Import Success

Request body:

```json
{
  "items": [
    {
      "type": "domain",
      "value": "Bulk-One.Example.com",
      "source": "manual-import",
      "tags": ["bulk"],
      "metadata": {"owner": "security"}
    },
    {
      "type": "subdomain",
      "value": "Api.Bulk-One.Example.com",
      "tags": ["api"]
    }
  ]
}
```

Request:

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"type":"domain","value":"Bulk-One.Example.com","source":"manual-import","tags":["bulk"],"metadata":{"owner":"security"}},{"type":"subdomain","value":"Api.Bulk-One.Example.com","tags":["api"]}]}'
```

Expected result: HTTP 200 with `created`, `updated`, `failed`, and `errors`.

### Bulk Import Partial Failure

Request body:

```json
{
  "items": [
    {"type": "domain", "value": "valid-import.example.com"},
    {"type": "domain", "value": ""},
    {"type": "unsupported", "value": "bad.example.com"}
  ]
}
```

Request:

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"type":"domain","value":"valid-import.example.com"},{"type":"domain","value":""},{"type":"unsupported","value":"bad.example.com"}]}'
```

Expected result: HTTP 207 when at least one record is accepted and at least one
record fails. If all records fail record-level validation, expected result is
HTTP 422.

### Bulk Import Rate Limit

Request body:

```json
{"items":[{"type":"domain","value":"rate-limit-import.example.com"}]}
```

Request:

```bash
for i in {1..11}; do
  curl -i -X POST http://localhost:8000/assets/import \
    -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"items\":[{\"type\":\"domain\",\"value\":\"rate-limit-import-$i.example.com\"}]}"
done
```

Expected result: the first 10 import attempts within 60 seconds are processed;
the 11th returns HTTP 429 with `details.operation` set to `bulk_import`.

### Viewer Import Is Forbidden

Request body:

```json
{"items":[{"type":"domain","value":"viewer-import.example.com"}]}
```

Request:

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"type":"domain","value":"viewer-import.example.com"}]}'
```

Expected result: HTTP 403. Viewer requests are blocked by RBAC before import
rate-limit checks.

### Relationship Creation And Duplicate Prevention

Create a second asset first:

```bash
TARGET_CREATE=$(curl -s -X POST http://localhost:8000/assets \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"ip","value":"203.0.113.10","source":"manual-test"}')
TARGET_ASSET_ID=$(echo "$TARGET_CREATE" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
```

Request body:

```json
{
  "source_asset_id": "<asset_id>",
  "target_asset_id": "<target_asset_id>",
  "relationship_type": "resolves_to",
  "metadata": {"source": "manual-test"}
}
```

Request:

```bash
curl -i -X POST http://localhost:8000/relationships \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"source_asset_id\":\"$ASSET_ID\",\"target_asset_id\":\"$TARGET_ASSET_ID\",\"relationship_type\":\"resolves_to\",\"metadata\":{\"source\":\"manual-test\"}}"
```

Expected result: HTTP 201. Repeating the same request returns HTTP 409 with
`DUPLICATE_RELATIONSHIP`.

### Graph Retrieval And Cache

Request:

```bash
curl -i "http://localhost:8000/assets/$ASSET_ID/graph" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"
```

Expected result: HTTP 200 with `center`, `nodes`, and `edges`. Repeating the
same request returns `X-Cache: HIT`, while the response shape and tenant scope
remain unchanged.

### Cache Fallback When Redis Is Unavailable

Request:

```bash
docker compose stop redis

curl -i "http://localhost:8000/assets?page=1&page_size=20" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"

curl -i "http://localhost:8000/assets/$ASSET_ID/graph" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"

docker compose start redis
```

Expected result: reads still return HTTP 200 with correct organization-scoped
database results while Redis is stopped, with `X-Cache: BYPASS`.

### Sample-Shaped Import

The import endpoint also accepts evaluator sample records with import-local
`id`, `parent`, and `covers` references. Relationship references are resolved
only inside the authenticated import batch.

```bash
curl -i -X POST http://localhost:8000/assets/import \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"id":"a1","type":"domain","value":"example.com","source":"assessment-sample","tags":["external"],"metadata":{}},{"id":"a2","type":"subdomain","value":"api.example.com","source":"assessment-sample","tags":["api"],"metadata":{},"parent":"a1"},{"id":"a3","type":"certificate","value":"cert-api-example","source":"assessment-sample","tags":["tls"],"metadata":{"issuer":"Example CA","expires":"2026-07-15"},"covers":"a2"}]}'
```

Expected result: valid assets are created or refreshed, the subdomain gets a
`parent` relationship to the domain, the certificate gets a `covers`
relationship to the subdomain, malformed records are reported per record, and
unresolved or unsafe references do not create relationships.

### Certificate Lifecycle

Certificate lifecycle status is derived from `metadata.expires`; it is not
stored as a separate source of truth. Responses classify certificates as
`expired`, `expiring_soon`, `valid`, or `unknown`.

```bash
curl -s "http://localhost:8000/assets?type=certificate&certificate_lifecycle_status=expired" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"

curl -s "http://localhost:8000/assets?type=certificate&certificate_lifecycle_status=expiring_soon" \
  -H "Authorization: Bearer $VIEWER_ACCESS_TOKEN"
```

The same classifier is used by asset detail responses, asset lists, graph
certificate nodes, import reporting for malformed expiry values, and analysis
evidence. Expiring soon means the expiry date is from today through the next 30
calendar days, inclusive.

Example certificate records:

```json
[
  {"type": "certificate", "value": "expired-cert", "metadata": {"expires": "2020-01-01"}},
  {"type": "certificate", "value": "soon-cert", "metadata": {"expires": "2026-07-15"}},
  {"type": "certificate", "value": "valid-cert", "metadata": {"expires": "2027-01-01"}},
  {"type": "certificate", "value": "missing-expiry", "metadata": {}},
  {"type": "certificate", "value": "bad-expiry", "metadata": {"expires": "not-a-date"}}
]
```

### Analysis Reports

Authenticated users can request a grounded report from organization-owned
evidence only. The endpoint selects real assets from PostgreSQL first, passes
only that bounded evidence to LangChain, asks for structured output, and then
validates every returned evidence ID before responding:

```bash
curl -i -X POST http://localhost:8000/analysis/report \
  -H "Authorization: Bearer $ANALYST_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"certificate","certificate_lifecycle_status":"expiring_soon","limit":25}'
```

Expected result: HTTP 200 with `status`, `summary`, `risks`,
`evidence_asset_ids`, and selected `evidence`. Empty matches return `status:
no_data` with no risks and no invented evidence. Missing provider settings
return HTTP 503 with `analysis_unavailable`; provider failures return HTTP 502
with `analysis_failed`; ungrounded provider output returns HTTP 502 with
`analysis_grounding_failed`. Responses must not include secrets, prompts,
provider stack traces, or cross-organization details.

The AI analysis route uses the `RATE_LIMIT_AI_ANALYSIS_ATTEMPTS` policy and the
same authenticated caller identity pattern as other protected workflows. Tests
mock the LangChain output so local and CI verification do not require a live
model call.

### Tenant Isolation

Log in as the other organization admin:

```bash
OTHER_LOGIN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"other-admin@example.com","password":"password123"}')
OTHER_ACCESS_TOKEN=$(echo "$OTHER_LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
```

Request:

```bash
curl -i "http://localhost:8000/assets/$ASSET_ID" \
  -H "Authorization: Bearer $OTHER_ACCESS_TOKEN"
```

Expected result: HTTP 404 with `ASSET_NOT_FOUND`; the API does not disclose
that the asset exists in another organization.

### CI Workflow

Request body: not applicable; this is a repository workflow test.

Manual check:

```bash
git push
```

Expected result: GitHub Actions runs the `Quality` workflow on `push` and
`pull_request`, syncs locked dependencies, then runs Ruff, pytest, and mypy.

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
uv sync --all-groups
docker compose up -d db redis
uv run alembic upgrade head
uv run python scripts/seed.py
uv run ruff check app tests
uv run pytest
uv run mypy app
```

These commands are the local quality gate for the final submission. GitHub Actions runs the
same locked dependency sync, Ruff lint, pytest suite, and mypy check on `push`
and `pull_request`. To validate failure visibility, open a temporary change
that breaks linting or a test, confirm the named workflow step fails, then
revert the intentional failure and confirm the workflow passes.

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

The Phase 6 rate-limit and cache contract lives at
`specs/006-test-ci-rate-limits/contracts/test-ci-rate-limits-api.yaml` and adds
structured HTTP 429 responses for login, refresh, and bulk import, plus
cache-behavior documentation for asset list and graph reads.

The Phase 7 contracts live under
`specs/007-analysis-submission-polish/contracts/` and cover:

```text
POST /analysis/report
GET /assets with certificate_lifecycle_status filters
POST /assets/import with id, parent, and covers sample references
```

## Final Submission Readiness

From a clean checkout:

```bash
uv sync --all-groups
docker compose up -d db redis
uv run alembic upgrade head
uv run python scripts/seed.py
uv run pytest
uv run ruff check app tests
uv run mypy app
```

Verify setup, seeded credential login, authenticated asset import, lifecycle
filters, relationships, graph retrieval, rate-limit behavior, analysis report
responses, and cache fallback. Known tradeoffs: live asset scanning is not
implemented, public registration and organization creation are intentionally
absent, users belong to one organization, organization switching is not
implemented, reports are generated on request rather than stored as report
history, and future AI analysis provider adapters can be added behind the same
LangChain-style provider boundary and grounding checks. The documented typing
gate is `uv run mypy app`; the stricter `uv run mypy app tests` command also
checks older test fixtures and currently reports legacy test annotation debt
outside the application package.
