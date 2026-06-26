# Feature Specification: Multi-Tenant Auth

**Feature Branch**: `[002-multi-tenant-auth]`

**Created**: 2026-06-26

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 2 ONLY."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seed Evaluation Tenants and Users (Priority: P1)

As an evaluator or developer, I need seeded organizations and users with known credentials, so I can test authentication, roles, and tenant isolation without public onboarding flows.

**Why this priority**: Phase 2 intentionally excludes public registration and organization creation. Seeded data is the only supported way to create users and organizations for local development and evaluation.

**Independent Test**: Run the documented seed workflow, then verify the expected organization and users exist and can be used for authentication.

**Acceptance Scenarios**:

1. **Given** an empty development database, **When** the seed workflow is run, **Then** it creates a demo organization with admin, analyst, and viewer users, plus a second organization with its own admin user, all with documented credentials.
2. **Given** the seed workflow has already run once, **When** it is run again, **Then** it completes without creating duplicate organizations or duplicate users.
3. **Given** the seeded users exist, **When** their accounts are inspected, **Then** each user belongs to exactly one organization and has exactly one role.

---

### User Story 2 - Authenticate Seeded Users (Priority: P1)

As a seeded user, I need to log in, refresh my session, log out, and inspect my own identity, so I can access protected asset-management features securely.

**Why this priority**: Authentication is the foundation for all protected Phase 2 and later behavior, including tenant scoping and role-based permissions.

**Independent Test**: Use a seeded user's credentials to log in, call the current-user endpoint with the returned access token, refresh the session with the refresh token, and then log out.

**Acceptance Scenarios**:

1. **Given** a seeded active user and valid credentials, **When** the user logs in, **Then** the system returns an access token and a refresh token.
2. **Given** a valid access token, **When** the user requests their current profile, **Then** the response identifies the user, organization, role, and active status.
3. **Given** a valid unexpired refresh token, **When** the user requests a refresh, **Then** the system issues a new access token.
4. **Given** a refresh token has been logged out, expired, or revoked, **When** it is used to refresh a session, **Then** the request is rejected.

---

### User Story 3 - Enforce Tenant Ownership (Priority: P1)

As an organization user, I need all tenant-owned data to be isolated to my organization, so another organization cannot read, modify, or relate my assets.

**Why this priority**: Tenant isolation is the project's highest security invariant and is required before asset CRUD, imports, and relationship features can be safely added.

**Independent Test**: Seed or create two organizations with users, create or prepare assets for both organizations, then verify each user's protected operations only see and affect their own organization's records.

**Acceptance Scenarios**:

1. **Given** two organizations contain the same asset type and value, **When** users from each organization access their assets, **Then** each organization can store and retrieve its own copy independently.
2. **Given** a user from one organization references an asset owned by another organization, **When** the user attempts to read or modify that asset through a protected operation, **Then** the system denies access or reports the asset as unavailable.
3. **Given** a relationship request references assets from different organizations, **When** the relationship is submitted, **Then** the system rejects the relationship.

---

### User Story 4 - Apply Role-Based Access (Priority: P1)

As a system maintainer, I need viewer, analyst, and admin permissions enforced consistently, so protected operations match each user's intended authority.

**Why this priority**: Later asset-management features rely on these permission boundaries. Implementing them in Phase 2 prevents later routes from inventing inconsistent authorization behavior.

**Independent Test**: Authenticate as each seeded role and verify read, write, relationship, import, stale-marking, and delete/archive permissions are allowed or denied according to the role matrix.

**Acceptance Scenarios**:

1. **Given** a viewer is authenticated, **When** they attempt read operations, **Then** the operations are allowed.
2. **Given** a viewer is authenticated, **When** they attempt create, update, import, stale-marking, relationship creation, or delete/archive operations, **Then** the operations are forbidden.
3. **Given** an analyst is authenticated, **When** they attempt create, update, import, stale-marking, or relationship creation operations, **Then** the operations are allowed.
4. **Given** an analyst is authenticated, **When** they attempt delete/archive operations, **Then** the operations are forbidden.
5. **Given** an admin is authenticated, **When** they perform any viewer or analyst operation or delete/archive operation, **Then** the operation is allowed.

---

### User Story 5 - Establish Tenant-Owned Inventory Records (Priority: P2)

As a backend developer preparing later phases, I need the core organization, user, token, asset, and relationship records defined with ownership and uniqueness rules, so future asset CRUD and graph work can build on correct data boundaries.

**Why this priority**: Phase 2 must create the security and data ownership foundation, even though the full asset CRUD, import, and graph behavior are implemented in later phases.

**Independent Test**: Apply the database changes and verify the required records, ownership links, uniqueness rules, and indexes exist through migration checks and focused data-integrity tests.

**Acceptance Scenarios**:

1. **Given** the database changes are applied, **When** the schema is inspected, **Then** organizations, users, refresh tokens, assets, and asset relationships are represented.
2. **Given** a user record exists, **When** its ownership and role are inspected, **Then** it has exactly one organization and one organization-level role.
3. **Given** two organizations create the same asset type and value, **When** both records are saved, **Then** both are allowed because uniqueness is scoped per organization.
4. **Given** one organization attempts to create the same asset type and value twice, **When** the duplicate is saved, **Then** the system prevents the duplicate.

### Edge Cases

- Invalid login credentials must be rejected without revealing whether the email or password was incorrect.
- Inactive users must not receive usable access or refresh tokens.
- Expired, revoked, malformed, unknown, or reused refresh tokens must be rejected.
- Raw passwords and raw refresh tokens must never be stored or logged.
- Access tokens missing user, organization, role, or expiry claims must be rejected by protected routes.
- Clients must not be able to set or override organization ownership on tenant-owned resources.
- Cross-organization asset and relationship references must fail even when the referenced identifiers are otherwise valid.
- Duplicate emails, organization slugs, organization-scoped assets, and organization-scoped relationships must be prevented.
- Public registration, public organization creation, membership management, and organization switching must remain unavailable.
- Required authentication and secret configuration must be documented and must not expose secret values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST represent organizations with a unique human-readable slug, display name, creation timestamp, and update timestamp.
- **FR-002**: System MUST represent users with a unique email, password hash, active status, creation timestamp, update timestamp, exactly one organization, and exactly one role.
- **FR-003**: System MUST support exactly three organization-level roles for this phase: viewer, analyst, and admin.
- **FR-004**: System MUST represent refresh tokens as user-owned records that store only a token hash, expiration timestamp, optional revocation timestamp, and creation timestamp.
- **FR-005**: System MUST represent assets as organization-owned records with type, value, status, first-seen timestamp, last-seen timestamp, source, tags, metadata, creation timestamp, and update timestamp.
- **FR-006**: System MUST represent asset relationships as organization-owned records connecting a source asset to a target asset with a relationship type, metadata, and creation timestamp.
- **FR-007**: System MUST enforce unique organization slugs.
- **FR-008**: System MUST enforce unique user emails.
- **FR-009**: System MUST enforce asset uniqueness by organization, type, and value.
- **FR-010**: System MUST enforce relationship uniqueness by organization, source asset, target asset, and relationship type.
- **FR-011**: System MUST NOT create a membership record type; each user belongs directly to exactly one organization.
- **FR-012**: System MUST provide a seed workflow that creates a demo organization with seeded admin, analyst, and viewer users with documented credentials.
- **FR-013**: System MUST provide a seed workflow that creates a second organization with a seeded admin user with documented credentials to support tenant isolation tests.
- **FR-014**: System MUST make the seed workflow repeatable without creating duplicate seeded organizations or users.
- **FR-015**: System MUST provide login, refresh, logout, and current-user endpoints for seeded users.
- **FR-016**: System MUST NOT provide public registration, public organization creation, or organization switching endpoints.
- **FR-017**: System MUST verify user passwords against stored password hashes during login.
- **FR-018**: System MUST issue a short-lived access token and longer-lived refresh token after successful login.
- **FR-019**: Access tokens MUST include user id, organization id, role, and expiry claims.
- **FR-020**: Protected routes MUST reject missing, malformed, expired, or otherwise invalid access tokens.
- **FR-021**: Current-user resolution MUST derive the authenticated user's organization and role from trusted authentication context.
- **FR-022**: System MUST derive tenant ownership from authenticated organization context for tenant-owned resources.
- **FR-023**: System MUST NOT accept or trust organization ownership supplied by clients for tenant-owned resources.
- **FR-024**: Every tenant-owned asset and relationship query MUST be scoped to the authenticated user's organization.
- **FR-025**: System MUST reject or hide cross-organization asset access according to the project's structured error strategy.
- **FR-026**: System MUST reject relationships where the source and target assets do not both belong to the authenticated user's organization.
- **FR-027**: System MUST enforce viewer permissions for reading assets, relationships, and graph data.
- **FR-028**: System MUST enforce analyst permissions for all viewer actions plus asset creation, asset updates, bulk import, stale marking, and relationship creation.
- **FR-029**: System MUST enforce admin permissions for all analyst actions plus asset delete/archive operations.
- **FR-030**: System MUST reject forbidden actions with a clear authorization failure.
- **FR-031**: Refresh tokens MUST expire and expired refresh tokens MUST be rejected.
- **FR-032**: Logout MUST revoke the submitted refresh token.
- **FR-033**: Refresh token validation MUST reject revoked refresh tokens.
- **FR-034**: System SHOULD rotate refresh tokens during refresh when feasible within the phase scope.
- **FR-035**: System MUST never log raw refresh tokens.
- **FR-036**: System MUST never store raw refresh tokens or raw passwords.
- **FR-037**: System MUST include tests for seeded login, refresh token behavior, logout revocation, RBAC decisions, and tenant isolation.
- **FR-038**: System MUST document seed instructions, seeded credentials, authentication flow, role permissions, and the absence of public onboarding endpoints in the README.
- **FR-039**: System MUST document any new required environment variables in `.env.example`.

### Key Entities

- **Organization**: A tenant boundary that owns users, assets, and relationships. It has a unique slug and display name.
- **User**: A seeded account that belongs to exactly one organization and has one role controlling its allowed actions.
- **Refresh Token**: A revocable, expiring session credential owned by one user and stored only as a hash.
- **Asset**: An organization-owned attack-surface item, such as a domain, subdomain, IP address, service, certificate, or technology.
- **Asset Relationship**: An organization-owned link between two assets in the same organization.
- **Role Permission**: The allowed action set for viewer, analyst, and admin users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can apply the Phase 2 database changes and run the seed workflow successfully from a clean Phase 1 database.
- **SC-002**: The seed workflow creates exactly four required seeded users with documented credentials: admin, analyst, and viewer in the demo organization, plus admin in a second organization.
- **SC-003**: Re-running the seed workflow produces zero duplicate seeded users and zero duplicate seeded organizations.
- **SC-004**: 100% of seeded active users can log in with documented credentials and receive both an access token and a refresh token.
- **SC-005**: 100% of protected endpoint checks reject unauthenticated requests.
- **SC-006**: Access tokens issued by the system contain user id, organization id, role, and expiry claims in every successful login.
- **SC-007**: 100% of expired, revoked, malformed, or unknown refresh token test cases are rejected.
- **SC-008**: Logout revokes the submitted refresh token, and the same token cannot be used afterward.
- **SC-009**: Viewer, analyst, and admin authorization tests match the documented role matrix in every covered operation category.
- **SC-010**: Two organizations can store identical asset type and value pairs independently, while duplicates within one organization are rejected.
- **SC-011**: Cross-organization asset access and cross-organization relationship creation are blocked in 100% of tenant isolation tests.
- **SC-012**: The API surface exposes login, refresh, logout, and current-user auth endpoints, and exposes no public registration, organization creation, or organization switching endpoints.
- **SC-013**: README and `.env.example` include all required Phase 2 setup, seed, credential, authentication, and configuration notes without committing secrets.

## Assumptions

- Phase 1 has already established the backend application foundation, database connectivity, migration workflow, configuration management, tests, and README setup notes.
- Organizations and users are created only through the seed workflow for this project version.
- Each user belongs to exactly one organization and has exactly one organization-level role.
- Public user registration, public organization creation, team management, invitations, email verification, password reset, billing, and organization switching are out of scope.
- Asset CRUD, bulk import behavior, lifecycle transitions, full relationship APIs, graph retrieval, rate limiting, caching, CI expansion, and LangChain analysis are later phases unless needed only to prove Phase 2 isolation and permission foundations.
- Cross-organization access may be reported as forbidden or unavailable, as long as the behavior is consistent with the project's structured error strategy and does not leak tenant data.
- Refresh token rotation is preferred but may be treated as a best-effort enhancement if the rest of the Phase 2 security foundation is complete.
