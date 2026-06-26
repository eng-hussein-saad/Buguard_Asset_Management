# Buguard Asset Management Backend

The backend provides the FastAPI foundation for Buguard Asset Management plus
the Phase 2 multi-tenant authentication slice. It includes health checks, async
PostgreSQL sessions, Alembic migrations, seeded evaluation tenants, login,
refresh, logout, current-user auth, tenant ownership helpers, and reusable RBAC
checks.

Public registration, public organization creation, membership management,
organization switching, full asset CRUD, bulk import, graph retrieval, caching,
and AI analysis are out of scope for this phase.

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
uv run pytest
uv run ruff check .
uv run mypy app
```

All three commands are part of the Phase 1 completion gate.

## Contract

The Phase 1 HTTP contract is limited to:

```text
GET /health
```

Response:

```json
{"status":"ok"}
```

The source contract lives at
`specs/001-backend-foundation/contracts/openapi.yaml`.
