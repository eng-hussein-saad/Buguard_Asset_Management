# Phase 4 Quickstart: Bulk Import Lifecycle

## Prerequisites

1. Install dependencies with `uv sync`.
2. Start PostgreSQL through Docker Compose or provide a valid `DATABASE_URL`.
3. Apply migrations with `uv run alembic upgrade head`.
4. Seed organizations and users with `uv run python scripts/seed.py`.

Seeded users expected from earlier phases:

- `admin@example.com / password123`
- `analyst@example.com / password123`
- `viewer@example.com / password123`
- `other-admin@example.com / password123`

## Run The API

```powershell
uv run uvicorn app.main:app --reload
```

Open the interactive API docs at `http://127.0.0.1:8000/docs`.

## Authenticate

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"analyst@example.com","password":"password123"}'

$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
```

## Import A Dataset

```powershell
$body = @{
  items = @(
    @{
      type = "domain"
      value = "Example.com"
      source = "sample-dataset"
      tags = @("external", "phase4")
      metadata = @{ registrar = "Example Registrar" }
    },
    @{
      type = "subdomain"
      value = "API.Example.com"
      source = "sample-dataset"
      tags = @("api")
      metadata = @{ owner = "platform" }
    }
  )
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/assets/import" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Expected outcome:

- HTTP 200
- Response includes `created = 2`, `updated = 0`, `failed = 0`, and `errors = []`.
- Created assets are scoped to the analyst user's organization.
- Domain-like values are canonicalized consistently with Phase 3.

## Re-Import The Same Dataset

Run the same import request again.

Expected outcome:

- HTTP 200
- Asset count for the organization does not increase.
- Response reports existing assets as `updated`.
- Existing `first_seen` values remain unchanged.
- `last_seen` values refresh to server processing time.

## Validate Tag And Metadata Merge

Import the domain again with new tags and metadata:

```powershell
$mergeBody = @{
  items = @(
    @{
      type = "domain"
      value = "example.com"
      tags = @("external", "priority")
      metadata = @{ registrar = "Updated Registrar"; environment = "prod" }
    }
  )
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/assets/import" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $mergeBody
```

Expected outcome:

- Existing tag `external` is not duplicated.
- New tag `priority` is added.
- Metadata key `registrar` uses the newest value.
- Metadata key `environment` is added.
- Existing non-conflicting metadata remains available.

## Validate Partial Failure Handling

```powershell
$partialBody = @{
  items = @(
    @{ type = "domain"; value = "valid.example.com" },
    @{ type = "domain"; value = "" },
    @{ type = "unsupported"; value = "bad.example.com" }
  )
} | ConvertTo-Json -Depth 8

Invoke-WebRequest `
  -Method Post `
  -Uri "http://127.0.0.1:8000/assets/import" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $partialBody
```

Expected outcome:

- HTTP 207 Multi-Status.
- Valid records are created or updated.
- Failed records appear in `errors` with original zero-based indexes and
  readable reasons.
- Response shape still includes `created`, `updated`, `failed`, and `errors`.

## Validate All-Record Failure Handling

```powershell
$failureBody = @{
  items = @(
    @{ type = "domain"; value = "" },
    @{ type = "unsupported"; value = "bad.example.com" }
  )
} | ConvertTo-Json -Depth 8

Invoke-WebRequest `
  -Method Post `
  -Uri "http://127.0.0.1:8000/assets/import" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $failureBody
```

Expected outcome:

- HTTP 422.
- No assets are created or updated.
- Response uses the same import summary shape.

## Validate Stale Lifecycle Behavior

1. Create or import an active asset.
2. Mark it stale through the existing asset update route:

```powershell
Invoke-RestMethod `
  -Method Patch `
  -Uri "http://127.0.0.1:8000/assets/$assetId" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"status":"stale"}'
```

Expected outcome:

- Analyst/admin users can mark their organization's asset as stale.
- Viewer users receive a structured authorization error.
- Missing or cross-organization asset IDs return the Phase 3 structured
  asset-not-found response.
- Re-importing the stale asset changes it back to `active`.

## Validate Archived Lifecycle Behavior

1. Create or update an asset to `archived` using admin credentials.
2. Re-import the same asset without `status`.

Expected outcome:

- The asset remains `archived`.
- The import summary counts the accepted record as `updated`.

3. Re-import the same asset with `status = "active"`.

Expected outcome:

- The asset becomes `active`.
- The import summary counts the accepted record as `updated`.

## Validate Tenant Isolation

1. Import `example.com` as `analyst@example.com`.
2. Authenticate as `other-admin@example.com`.
3. Import `example.com` for the second organization.
4. List assets for each organization.

Expected outcome:

- Both organizations can store the same type/value independently.
- Imports in one organization do not create, update, or reveal assets in the
  other organization.

## Verification Commands

```powershell
uv run pytest tests/contract tests/integration tests/unit
uv run ruff check .
uv run mypy app
```

If Phase 4 changes evaluator-facing import instructions, update `README.md`.
If implementation introduces a new setting, document it in `.env.example`;
otherwise no `.env.example` change is required.
