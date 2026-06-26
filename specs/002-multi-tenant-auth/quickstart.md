# Quickstart: Multi-Tenant Auth

This guide validates the Phase 2 behavior end to end after implementation.

## Prerequisites

- Python 3.13
- uv
- Docker Compose with PostgreSQL available
- Phase 1 application foundation already working

## Environment

Update `.env.example` and local `.env` with Phase 2 settings:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/buguard
JWT_SECRET_KEY=change-me-in-local-dev
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Secret values must be local-only and must not be committed.

## Install Dependencies

```bash
uv add "python-jose[cryptography]" "passlib[bcrypt]"
uv sync
```

## Apply Database Changes

```bash
uv run alembic upgrade head
```

Expected outcome: tables exist for organizations, users, refresh tokens,
assets, and asset relationships with the constraints described in
[data-model.md](./data-model.md).

## Seed Evaluation Data

```bash
uv run python scripts/seed.py
uv run python scripts/seed.py
```

Expected outcome: the second run completes without duplicate organizations or
users.

Required seeded users:

```text
admin@example.com / password123
analyst@example.com / password123
viewer@example.com / password123
other-admin@example.com / password123
```

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

## Validate Auth Flow

Log in:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}'
```

Expected outcome: response includes `access_token`, `refresh_token`,
`token_type: bearer`, and `expires_in: 900`.

Check current user:

```bash
curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Expected outcome: response includes user id, email, organization id, role, and
active status.

Refresh session:

```bash
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

Expected outcome: response includes a new access token and a replacement
refresh token. Reusing the submitted refresh token is rejected.

Logout:

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<replacement_refresh_token>"}'
```

Expected outcome: 204 No Content. Refreshing with the logged-out token is
rejected.

## Validate RBAC and Tenant Isolation

Run the automated Phase 2 test set:

```bash
uv run pytest tests/contract tests/integration tests/unit
```

Expected outcomes:

- Viewer can read protected asset/relationship/graph categories when those
  endpoints exist, but cannot write.
- Analyst can write and create relationships, but cannot delete/archive.
- Admin can perform analyst actions and delete/archive.
- Protected routes reject unauthenticated requests.
- Two organizations can store identical asset type/value pairs independently.
- Cross-organization asset access returns 404 Not Found.
- Cross-organization relationship creation is rejected.

## Quality Checks

```bash
uv run ruff check .
uv run mypy app
uv run pytest
```

Expected outcome: all checks pass before Phase 2 is considered complete.

## Documentation Checks

README must document:

- Seed command and seeded credentials
- Login, refresh, logout, and current-user flow
- Role permission matrix
- Tenant isolation rule that `organization_id` is derived from auth context
- Absence of public registration, public organization creation, membership
  management, and organization switching
- New environment variables and default token lifetimes
