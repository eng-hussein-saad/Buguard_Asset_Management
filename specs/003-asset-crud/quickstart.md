# Quickstart: Asset CRUD

## Prerequisites

- PostgreSQL is available through Docker Compose or `DATABASE_URL`.
- Phase 2 migrations and seed users are available.
- No public registration or organization creation is required.

## Setup

```bash
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload
```

Open API documentation at:

```text
http://localhost:8000/docs
```

## Authenticate Seeded Users

Use the seeded users from `PLAN.md`:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"password123"}'
```

Expected outcome: HTTP 200 with `access_token`, `refresh_token`, `token_type`,
and `expires_in`.

Repeat for:

- `admin@example.com` to verify hard delete.
- `viewer@example.com` to verify read-only access.
- `other-admin@example.com` to verify tenant isolation.

## Create an Asset

```bash
curl -X POST http://localhost:8000/assets \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "domain",
    "value": " Example.COM ",
    "status": "active",
    "source": "manual",
    "tags": ["external", "production"],
    "metadata": {"owner": "security"}
  }'
```

Expected outcome: HTTP 201. The response belongs to the authenticated user's
organization, does not require client ownership input, and returns normalized
`value: "example.com"`.

## Reject Client Ownership

```bash
curl -X POST http://localhost:8000/assets \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"organization_id":"00000000-0000-0000-0000-000000000000","type":"domain","value":"bad.example"}'
```

Expected outcome: validation error because `organization_id` is not accepted.

## Reject Duplicate Create

Submit the same normalized `type` and `value` again in the same organization.

Expected outcome: HTTP 409 with structured error envelope:

```json
{
  "error": {
    "code": "DUPLICATE_ASSET",
    "message": "Asset already exists.",
    "details": {}
  }
}
```

## List, Filter, Sort, and Paginate

```bash
curl "http://localhost:8000/assets?type=domain&tag=external&source=manual&value_contains=example&sort_by=value&sort_order=asc&page=1&page_size=20" \
  -H "Authorization: Bearer <viewer_access_token>"
```

Expected outcome: HTTP 200 with `items`, `page`, `page_size`, `total`,
`total_pages`, `has_next`, and `has_previous`. Results include only assets owned
by the authenticated user's organization.

## Read and Update an Asset

```bash
curl http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <viewer_access_token>"
```

Expected outcome: HTTP 200 for an asset in the viewer's organization.

```bash
curl -X PATCH http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <analyst_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"stale","tags":["external","review"]}'
```

Expected outcome: HTTP 200 with updated fields and unchanged organization
ownership.

## Hard Delete

```bash
curl -X DELETE http://localhost:8000/assets/<asset_id> \
  -H "Authorization: Bearer <admin_access_token>"
```

Expected outcome: HTTP 204. A later read returns HTTP 404 with code
`ASSET_NOT_FOUND`.

## Verify RBAC

- Viewer `POST /assets`, `PATCH /assets/{asset_id}`, and
  `DELETE /assets/{asset_id}` return HTTP 403 with `authorization_failed`.
- Analyst `DELETE /assets/{asset_id}` returns HTTP 403.
- Admin can create, update, and hard delete.

## Verify Tenant Isolation

1. Create the same `type` and `value` under the demo organization and the second
   organization.
2. List assets as each tenant.
3. Request another tenant's `asset_id` from detail, update, and delete routes.

Expected outcome: each tenant sees only its own copy, and cross-organization
asset identifiers return the structured asset-not-found error.

## Validation Commands

```bash
uv run pytest tests/unit/test_asset_normalization.py
uv run pytest tests/contract/test_assets_api.py
uv run pytest tests/integration/test_asset_crud.py tests/integration/test_asset_filters.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py
uv run pytest
uv run ruff check .
uv run mypy app
```

## Documentation Checks

- Confirm `GET /docs` shows an `Assets` group with summaries for create, list,
  detail, update, and delete.
- Confirm README explains Phase 3 asset create, query, update, delete, and test
  commands.
- Confirm `.env.example` remains current. Phase 3 does not require a new
  environment variable unless implementation introduces one.
