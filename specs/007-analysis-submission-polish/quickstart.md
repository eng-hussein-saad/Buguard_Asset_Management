# Quickstart: Analysis Submission Polish Validation

## Prerequisites

- Python 3.13 and `uv`
- Docker Compose
- PostgreSQL connection configured through `DATABASE_URL`
- Safe local values in `.env`, including analysis provider placeholders from
  `.env.example`

## Clean Startup

1. Copy `.env.example` to `.env` and fill local values.
2. Start dependencies with Docker Compose.
3. Run migrations.
4. Seed local organizations and users.
5. Confirm `/health` succeeds.

Expected outcome: the API starts, database migrations are current, seeded users
can authenticate, and missing analysis provider configuration does not prevent
core startup.

## Automated Verification

Run the full verification suite:

```bash
uv run pytest
uv run ruff check .
uv run mypy app tests
```

Expected outcome: tests and linting pass, or any final submission exception is
documented with a clear reason in README.

## Analysis Report Validation

1. Authenticate as a seeded user in organization A.
2. Import or create assets in organization A, including certificates with:
   expired, expiring-soon, valid future, missing, and malformed
   `metadata.expires` values.
3. Authenticate as a seeded user in organization B and create overlapping asset
   values.
4. Request `POST /analysis/report` with filters.

Expected outcome: the report uses only organization A evidence, includes
evidence IDs for asset-specific risks, distinguishes expired from expiring-soon
certificates, returns no-data for empty matches, and returns structured
unavailable/failure responses when provider configuration is missing or failing.

## Certificate Lifecycle Validation

1. Read a certificate with `GET /assets/{asset_id}`.
2. List certificates with `GET /assets?type=certificate`.
3. Filter expired certificates with
   `GET /assets?type=certificate&certificate_lifecycle_status=expired`.
4. Filter expiring-soon certificates with
   `GET /assets?type=certificate&certificate_lifecycle_status=expiring_soon`.
5. Retrieve graph data for an asset connected to certificates.

Expected outcome: all surfaces derive lifecycle status from `metadata.expires`
using the same expired, expiring-soon, valid, or unknown classification, and no
filter or graph response leaks another organization's certificates.

## Sample-Shaped Import Validation

Import a dataset with records shaped like:

```json
{
  "items": [
    {
      "id": "a1",
      "type": "domain",
      "value": "example.com",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["external"],
      "metadata": {}
    },
    {
      "id": "a2",
      "type": "subdomain",
      "value": "api.example.com",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["api"],
      "metadata": {},
      "parent": "a1"
    },
    {
      "id": "a3",
      "type": "certificate",
      "value": "cert-api-example",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["tls"],
      "metadata": {
        "issuer": "Example CA",
        "expires": "2026-07-15"
      },
      "covers": "a2"
    }
  ]
}
```

Expected outcome: valid assets are created or refreshed, `parent` and `covers`
relationships are created inside the authenticated organization, malformed
records are reported without discarding unrelated valid records, and unresolved
references do not create unsafe relationships.

## Documentation Readiness Validation

Review README and `.env.example`.

Expected outcome: an evaluator can identify setup, container, migration, seed,
seeded credentials, authentication examples, import examples, lifecycle filters,
relationships, graph usage if present, rate limits, required analysis behavior,
known tradeoffs, future improvements, and scope assumptions:

- No public registration.
- No public organization creation.
- Each user belongs to exactly one organization and has one role.
- Organization ownership comes from authenticated context, never client input.
- Supporting users across multiple organizations is a future enhancement.
- Live scanning and asset discovery are out of scope.
