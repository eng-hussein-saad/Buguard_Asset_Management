# Quickstart: Asset Relationships Graph

## Prerequisites

- PostgreSQL is running and `DATABASE_URL` points at the local database.
- Dependencies are installed with `uv sync`.
- Migrations are current.
- Seeded users from earlier phases are available.

## Setup

```powershell
uv run alembic upgrade head
uv run python scripts/seed.py
```

## Validate Relationship Creation

1. Authenticate as an analyst or admin.
2. Create or reuse two assets in the same organization.
3. Create a relationship:

```http
POST /relationships
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "source_asset_id": "<source-asset-id>",
  "target_asset_id": "<target-asset-id>",
  "relationship_type": "resolves_to",
  "metadata": {}
}
```

Expected outcome: `201 Created` with the relationship id, source asset id,
target asset id, relationship type, metadata, and created timestamp. The
response is scoped to the authenticated organization.

## Validate Duplicate Prevention

Repeat the same relationship creation request.

Expected outcome: `409 Conflict` with the structured error envelope. The
relationship count for the organization does not increase.

## Validate RBAC

Authenticate as a viewer and repeat the create request.

Expected outcome: `403 Forbidden` with the structured authorization error.
Viewer users can still list relationships and retrieve graphs.

## Validate Relationship Listing

```http
GET /relationships
Authorization: Bearer <access-token>
```

Expected outcome: `200 OK` with only relationships owned by the authenticated
organization. A user in another organization does not see these relationships.

## Validate One-Hop Graph Retrieval

```http
GET /assets/<asset-id>/graph
Authorization: Bearer <access-token>
```

Expected outcome: `200 OK` with `center`, `nodes`, and `edges`. The `nodes`
array includes the center asset and directly connected assets only. The `edges`
array includes relationships where the center asset is either the source or
target.

For an organization-owned asset with no relationships, expected outcome is the
center asset in both `center` and `nodes`, and an empty `edges` array.

## Validate Tenant Isolation

1. Authenticate as a user in organization A.
2. Attempt to create a relationship to an asset owned by organization B.
3. Request the graph for an asset owned by organization B.

Expected outcome: both requests behave as unavailable assets and do not reveal
organization B's data.

## Validate Visualization

Open the simple graph view and provide an organization-owned asset id.

Expected outcome: the view fetches `GET /assets/{asset_id}/graph`, displays
nodes labeled by asset value, displays edges labeled by relationship type, and
shows the structured error state when the graph endpoint fails.

## Automated Verification

```powershell
uv run pytest tests/contract tests/integration tests/unit
uv run pytest
uv run ruff check .
uv run mypy app
```

## Documentation and Configuration Checks

- Update README notes if relationship creation, graph retrieval, visualization
  usage, or evaluator-visible behavior changes.
- Update `.env.example` only if implementation introduces a new required
  environment variable. No new variable is planned for Phase 5.
