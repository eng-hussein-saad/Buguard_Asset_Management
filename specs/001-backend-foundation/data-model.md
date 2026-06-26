# Data Model: Backend Foundation

Phase 1 does not create tenant, user, asset, relationship, refresh-token, or
other domain persistence models. The "data model" for this phase is limited to
foundation concepts and configuration surfaces that later phases will build on.

## Application Service

**Purpose**: Backend API process that starts, loads configuration, registers
routes, and exposes operational health.

**Fields / Properties**:

- `app_name`: service display name used in metadata.
- `settings`: runtime configuration loaded from environment variables.
- `routes`: registered API route modules, including the health route.

**Validation Rules**:

- Application startup must load required settings before serving requests.
- Missing or malformed required settings must produce sanitized errors.
- Phase 1 must not register Phase 2+ endpoints.

## Health Check

**Purpose**: Minimal application availability response.

**Contract**:

- Method/path: `GET /health`
- Success status: `200`
- Response body: `{"status":"ok"}`

**Validation Rules**:

- Response body must be exactly the expected JSON object.
- Health reports application availability only; it does not become a database
  readiness check in Phase 1.

## Runtime Configuration

**Purpose**: Environment-provided settings needed to run locally or in Docker.

**Fields**:

- `DATABASE_URL` (required): PostgreSQL connection URL used by the API and
  Alembic configuration.

**Validation Rules**:

- `DATABASE_URL` is required for normal startup.
- Missing or malformed values fail startup with sanitized, understandable
  messages.
- `.env.example` must document placeholder values only.
- No secret values may be committed.

## Database Service

**Purpose**: PostgreSQL runtime used by the backend and future persisted data.

**Fields / Configuration**:

- Host, port, database, username, and password are represented through
  `DATABASE_URL` and Docker Compose environment values.

**Relationships**:

- Application Service connects to Database Service through async SQLAlchemy
  session setup.
- Alembic uses the same configuration surface for migration commands.

**Validation Rules**:

- Docker Compose must define a separate PostgreSQL service.
- API service must use `DATABASE_URL` to reach PostgreSQL in Docker Compose.

## Migration Foundation

**Purpose**: Alembic setup that tracks and applies future schema changes.

**Fields / Files**:

- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/`
- SQLAlchemy metadata import path prepared for future models.

**Validation Rules**:

- No placeholder schema migration is required in Phase 1.
- A documented no-op migration verification command must complete successfully
  before domain models exist.
- Future model discovery must be possible without reorganizing the foundation.

## State Transitions

No persisted domain entity state transitions exist in Phase 1.

## Deferred Domain Models

The following are explicitly out of scope for Phase 1 and must not be created:

- Organizations
- Users
- Memberships
- Refresh tokens
- Assets
- Asset relationships
- Imports
- AI analysis records
