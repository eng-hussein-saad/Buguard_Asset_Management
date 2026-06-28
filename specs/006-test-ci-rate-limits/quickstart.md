# Quickstart: Test CI Rate Limits

## Prerequisites

- Python 3.13 and uv are installed.
- Docker Compose is available for PostgreSQL and cache-backed validation.
- `.env` is created from `.env.example` and updated with local development
  values.
- Seeded users and organizations are available through the existing seed
  workflow; public registration is not required.

## Local Setup

```bash
uv sync --all-groups
docker compose up -d db redis
uv run alembic upgrade head
uv run python -m app.db.seed
```

If the cache service is not running, asset list and graph reads must still
return correct uncached organization-scoped responses.

## Quality Checks

```bash
uv run ruff check app tests
uv run pytest
uv run mypy app
```

Expected outcome: linting and the full automated test suite pass. Static type
checks should pass when Phase 6 implementation keeps the current mypy
configuration compatible.

## Continuous Quality Workflow Validation

1. Confirm `.github/workflows/` contains a workflow triggered by `push` and
   `pull_request`.
2. Confirm the workflow installs dependencies from the locked uv dependency
   set.
3. Confirm the workflow runs linting and pytest.
4. Confirm a deliberately broken lint or test change fails the workflow, then
   revert the broken change and confirm the workflow passes.

Expected outcome: maintainers can see the failing step when a required check
fails, and the overall workflow passes only when required checks pass.

## Rate-Limit Validation

### Login

1. Send 5 login attempts within 60 seconds for the same attempted username and
   client network identity.
2. Send a 6th login attempt within the same minute.

Expected outcome: the 6th request returns HTTP 429 with the structured
`rate_limited` error shape. Attempts below the threshold keep normal success or
invalid-credential behavior.

### Refresh

1. Authenticate as a seeded user and obtain a refresh token.
2. Send 10 refresh attempts within 60 seconds for the same authenticated user
   and organization.
3. Send an 11th refresh request within the same minute.

Expected outcome: the 11th request returns HTTP 429 with the structured
`rate_limited` error shape.

### Bulk Import

1. Authenticate as an analyst or admin seeded user.
2. Send 10 bulk import attempts within 60 seconds for the same authenticated
   user and organization.
3. Send an 11th import request within the same minute.

Expected outcome: the 11th request returns HTTP 429 before additional import
processing. Viewer users remain forbidden by RBAC independent of rate limits.

## Cache Validation

### Organization Isolation

1. Seed two organizations with overlapping asset values.
2. Authenticate as one user from each organization.
3. Read `GET /assets` and `GET /assets/{asset_id}/graph` for both
   organizations with equivalent inputs.

Expected outcome: cached and uncached responses include only assets, graph
nodes, and graph edges from the authenticated organization.

### Invalidation

1. Read an asset list and asset graph to populate cache entries.
2. Perform each relevant write in the authenticated organization: asset create
   or refresh, asset update, asset delete or archive, bulk import, relationship
   create or delete, and marking assets stale.
3. Repeat the same reads.

Expected outcome: repeated reads reflect the write and do not serve stale
cached payloads.

### Fallback

1. Stop or misconfigure the cache service in a local environment.
2. Read `GET /assets` and `GET /assets/{asset_id}/graph`.

Expected outcome: both reads return correct organization-scoped database
results without cross-tenant leakage. Writes still succeed when their database
work is valid, even if cache invalidation cannot reach the cache service.

## Documentation Validation

Confirm README and `.env.example` document:

- Local test commands.
- CI quality-check behavior.
- Seeded-user authentication expectations.
- Login, refresh, bulk import, and future AI analysis rate limits.
- Cache scoping, invalidation, and fallback behavior.
- Any new cache or rate-limit environment variables.
