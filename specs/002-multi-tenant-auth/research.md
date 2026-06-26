# Research: Multi-Tenant Auth

## Decision: Use direct user-to-organization ownership, not memberships

**Rationale**: The Phase 2 spec requires each user to belong to exactly one
organization and have exactly one role. A direct `users.organization_id` column
and `users.role` column keep authentication, tenant context, and RBAC simple
while still proving multi-tenant isolation.

**Alternatives considered**: A membership table with per-organization roles was
rejected because organization switching, invitations, team management, and
multi-organization users are out of scope.

## Decision: Store roles as a constrained enum-like string

**Rationale**: The allowed role set is fixed to `viewer`, `analyst`, and
`admin`. A constrained string keeps Pydantic validation and database checks
straightforward and avoids adding an unnecessary role table.

**Alternatives considered**: A roles table was rejected because permissions are
static for this assessment phase.

## Decision: Add JWT support with `python-jose[cryptography]`

**Rationale**: FastAPI projects commonly use python-jose for compact JWT
creation and validation. It supports signed claims for `sub`,
`organization_id`, `role`, and `exp`, which are required by the spec.

**Alternatives considered**: Hand-rolled token signing was rejected because JWT
parsing and expiry verification should use a maintained library.

## Decision: Add password hashing with `passlib[bcrypt]`

**Rationale**: The current dependencies do not include a password hashing
library. Passlib with bcrypt is a standard Python option for hashing seeded user
passwords and verifying login credentials.

**Alternatives considered**: Plain hashing through `hashlib` was rejected
because password hashing requires adaptive, salted hashing.

## Decision: Generate opaque refresh tokens and store only hashes

**Rationale**: Refresh tokens need revocation, expiry, and rotation. Generating
high-entropy opaque tokens and storing only a hash lets the server invalidate
tokens without exposing raw credentials in the database.

**Alternatives considered**: JWT refresh tokens were rejected because server-side
revocation and reuse detection are simpler with database-backed opaque tokens.

## Decision: Rotate refresh tokens on every successful refresh

**Rationale**: The clarified spec requires rotation. On refresh, the submitted
token is validated, revoked, and replaced with a new access token plus a new
refresh token. Reusing the old token is rejected.

**Alternatives considered**: Reusing refresh tokens until expiry was rejected
because it conflicts with the clarification and weakens stolen-token recovery.

## Decision: Use 15-minute access tokens and 7-day refresh tokens by default

**Rationale**: The clarified spec sets these defaults. They should be exposed in
configuration and documented in `.env.example`.

**Alternatives considered**: Hard-coding lifetimes was rejected because
operational settings belong in environment-driven configuration.

## Decision: Return 404 for cross-organization asset references

**Rationale**: The clarified spec requires not-found responses for
cross-tenant asset access so the API does not reveal whether another tenant's
asset exists.

**Alternatives considered**: Returning 403 was rejected because it can leak that
the referenced asset exists outside the caller's tenant.

## Decision: Define asset and relationship tables in Phase 2

**Rationale**: Full asset CRUD is later, but tenant isolation and uniqueness
must be represented now. Phase 2 migrations should create `assets` and
`asset_relationships` with organization ownership, constrained types/statuses,
relationship type constraints, and organization-scoped uniqueness.

**Alternatives considered**: Deferring asset tables to Phase 3 was rejected
because tenant isolation tests and relationship ownership rules require the
data model foundation in Phase 2.
