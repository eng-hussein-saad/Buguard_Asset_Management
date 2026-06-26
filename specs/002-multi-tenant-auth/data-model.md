# Data Model: Multi-Tenant Auth

## Organization

Represents one tenant boundary.

**Fields**

- `id`: UUID primary key
- `slug`: unique non-empty string, human-readable tenant identifier
- `name`: non-empty display name
- `created_at`: timezone-aware creation timestamp
- `updated_at`: timezone-aware update timestamp

**Relationships**

- Owns many users
- Owns many assets
- Scopes many asset relationships

**Validation and constraints**

- `slug` is globally unique.
- Seed workflow must create organizations idempotently by slug.

## User

Represents a seeded login account belonging to exactly one organization.

**Fields**

- `id`: UUID primary key
- `organization_id`: required foreign key to organizations
- `email`: globally unique normalized email
- `password_hash`: hashed password only
- `role`: one of `viewer`, `analyst`, `admin`
- `is_active`: boolean account status
- `created_at`: timezone-aware creation timestamp
- `updated_at`: timezone-aware update timestamp

**Relationships**

- Belongs to exactly one organization
- Owns many refresh token records

**Validation and constraints**

- `email` is globally unique.
- Raw passwords are never stored or logged.
- Inactive users cannot receive usable access or refresh tokens.
- No membership table is created for Phase 2.

## Refresh Token

Represents one revocable, expiring session credential.

**Fields**

- `id`: UUID primary key
- `user_id`: required foreign key to users
- `token_hash`: hash of the opaque refresh token
- `expires_at`: timezone-aware expiration timestamp
- `revoked_at`: nullable timezone-aware revocation timestamp
- `created_at`: timezone-aware creation timestamp

**Relationships**

- Belongs to one user

**Validation and constraints**

- Raw refresh tokens are returned only once to the client.
- Raw refresh tokens are never stored or logged.
- Expired, revoked, malformed, unknown, or reused refresh tokens are rejected.
- Successful refresh revokes the submitted token and creates a replacement.
- Logout revokes the submitted refresh token.

## Asset

Represents an organization-owned attack-surface item. Phase 2 creates the
foundation; full CRUD and import lifecycle behavior are later phases.

**Fields**

- `id`: UUID primary key
- `organization_id`: required foreign key to organizations
- `type`: one of `domain`, `subdomain`, `ip_address`, `service`,
  `certificate`, `technology`
- `value`: non-empty asset value
- `status`: one of `active`, `stale`, `archived`
- `first_seen`: timezone-aware timestamp
- `last_seen`: timezone-aware timestamp
- `source`: nullable source string
- `tags`: list/array of tag strings
- `metadata`: JSON object
- `created_at`: timezone-aware creation timestamp
- `updated_at`: timezone-aware update timestamp

**Relationships**

- Belongs to one organization
- Can be the source or target of many asset relationships in the same
  organization

**Validation and constraints**

- Unique by `(organization_id, type, value)`.
- Clients must not set or override `organization_id`.
- Tenant-scoped reads and writes must filter by authenticated organization.
- Cross-organization access returns 404 Not Found.

## Asset Relationship

Represents an organization-owned directed relationship between two assets.

**Fields**

- `id`: UUID primary key
- `organization_id`: required foreign key to organizations
- `source_asset_id`: required foreign key to assets
- `target_asset_id`: required foreign key to assets
- `relationship_type`: one of `belongs_to`, `resolves_to`, `runs_on`, `covers`,
  `detected_on`
- `metadata`: JSON object
- `created_at`: timezone-aware creation timestamp

**Relationships**

- Belongs to one organization
- Connects one source asset to one target asset

**Validation and constraints**

- Unique by `(organization_id, source_asset_id, target_asset_id,
  relationship_type)`.
- Source and target assets must both belong to the authenticated organization.
- Cross-organization relationship creation is rejected.
- Clients must not set or override `organization_id`.

## Role Permission

Represents the fixed action set implied by the user's role.

**Permissions**

- `viewer`: read assets, relationships, and graph data
- `analyst`: all viewer permissions plus asset creation, asset updates, bulk
  import, stale marking, and relationship creation
- `admin`: all analyst permissions plus delete/archive operations

**Validation and constraints**

- Forbidden actions return a clear authorization failure.
- Role checks must be reusable by later route modules.

## State Transitions

**Refresh token**

- `active` -> `revoked` when used for successful refresh
- `active` -> `revoked` when submitted to logout
- `active` -> `expired` when current time is after `expires_at`
- `revoked` or `expired` -> rejected when reused

**User**

- `active` users can authenticate.
- `inactive` users cannot receive new tokens and protected requests for inactive
  users are rejected.

**Asset**

- Phase 2 defines `active`, `stale`, and `archived`.
- Lifecycle transitions are implemented in later asset/import phases.
