# Feature Specification: Asset CRUD

**Feature Branch**: `[003-asset-crud]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 3 ONLY."

## Clarifications

### Session 2026-06-27

- Q: For Phase 3, what should `DELETE /assets/{asset_id}` do? -> A: Hard delete permanently removes the asset from the database.
- Q: When a user tries to create an asset with the same `type` and `value` as an existing asset in their organization, what should Phase 3 do? -> A: Reject duplicate create requests within the same organization with structured `409 Conflict`.
- Q: If a client includes `organization_id` in an asset create or update payload, what should Phase 3 do? -> A: Reject requests that include `organization_id` with a validation error.
- Q: How should Phase 3 handle invalid pagination parameters? -> A: Reject `page < 1`, `page_size < 1`, and `page_size > 100` with validation errors.
- Q: How should Phase 3 normalize asset `value` before storage, duplicate checks, and filtering? -> A: Trim all values; lowercase `domain` and `subdomain` values before storing and duplicate checks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Organization Assets (Priority: P1)

As an analyst or admin, I need to create, inspect, update, and remove assets within my organization, so the asset inventory can reflect the current attack surface without exposing another tenant's data.

**Why this priority**: Asset CRUD is the core operational surface for Phase 3. Later import, lifecycle, and relationship behavior depends on reliable tenant-scoped asset management.

**Independent Test**: Authenticate as analyst and admin users, create an asset without providing organization ownership, read it back, update allowed fields, and verify hard deletion is available only to an admin.

**Acceptance Scenarios**:

1. **Given** an analyst is authenticated, **When** they create an asset with valid type, value, status, source, tags, metadata, and timestamps, **Then** the asset is saved under the analyst's organization and returned without requiring or accepting organization ownership from the request.
2. **Given** an analyst is authenticated and owns an existing organization asset, **When** they update editable asset details, **Then** the response reflects the updated details and keeps the asset in the same organization.
3. **Given** an admin is authenticated and owns an existing organization asset, **When** they delete the asset, **Then** the asset is permanently removed from storage and subsequent reads return the asset-not-found response.
4. **Given** a viewer is authenticated, **When** they attempt to create, update, or delete an asset, **Then** the action is rejected with a structured forbidden error.

---

### User Story 2 - Find and Browse Assets (Priority: P1)

As a viewer, analyst, or admin, I need to list and read assets with useful filters, sorting, and pagination, so I can inspect the organization's attack surface quickly and predictably.

**Why this priority**: Read access is required for all roles and is the most common workflow for understanding current inventory.

**Independent Test**: Seed assets for two organizations, authenticate as each role, and verify list, detail, filter, sort, and pagination behavior only returns assets owned by the authenticated user's organization.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and their organization has assets, **When** they list assets without filters, **Then** they receive the first page of organization-owned assets using the default page and page size.
2. **Given** assets exist with different types, statuses, tags, sources, and values, **When** a user applies supported filters, **Then** only matching organization-owned assets are returned.
3. **Given** assets exist with sortable fields, **When** a user requests an allowed sort field and sort order, **Then** the returned assets are ordered predictably.
4. **Given** a user requests a specific asset owned by their organization, **When** the asset exists, **Then** the asset details are returned.

---

### User Story 3 - Preserve Tenant Isolation (Priority: P1)

As an organization user, I need asset operations to be strictly limited to my organization, so another organization cannot infer, read, change, or remove my assets.

**Why this priority**: Tenant isolation is a constitutional requirement and a critical security boundary for all asset-management behavior.

**Independent Test**: Create matching and distinct assets in two organizations, authenticate as users from each organization, and verify every asset CRUD and list operation is scoped to the authenticated user's organization.

**Acceptance Scenarios**:

1. **Given** two organizations contain identical asset type and value pairs, **When** users from each organization list or read assets, **Then** each user sees only their own organization's copy.
2. **Given** a user references an asset identifier owned by another organization, **When** they read, update, or delete that asset, **Then** the system responds as if the asset is unavailable to that user.
3. **Given** a client submits organization ownership in an asset create or update payload, **When** the request is processed, **Then** the request is rejected with a validation error and cannot change the authenticated organization scope.

---

### User Story 4 - Receive Clear Validation and Error Responses (Priority: P2)

As an API consumer, I need invalid requests and domain failures to return consistent, understandable responses, so client integrations can handle errors safely and users can correct mistakes.

**Why this priority**: Phase 3 includes API polish. Consistent validation, forbidden, and not-found behavior prevents confusing client behavior and supports readable OpenAPI documentation.

**Independent Test**: Submit invalid asset payloads, unsupported filters or sort options, missing assets, forbidden actions, and unauthenticated requests, then verify each response is consistent and documented.

**Acceptance Scenarios**:

1. **Given** a request contains an unsupported asset type or status, **When** the request is submitted, **Then** it is rejected with a validation response that identifies the invalid field.
2. **Given** a user requests an asset that does not exist or is outside their organization, **When** the request is processed, **Then** the system returns a structured not-found error using the asset-not-found domain code.
3. **Given** a user lacks permission for an asset action, **When** they submit the request, **Then** the system returns a structured forbidden error using a stable authorization code.
4. **Given** an API consumer views the generated API documentation, **When** they inspect the asset routes, **Then** each route has readable grouping, summaries, request shapes, response shapes, and error examples.

### Edge Cases

- Page numbers below 1, page sizes below 1, and page sizes above the allowed maximum must be rejected with validation errors.
- Empty result sets must return a successful paginated response with no items, not an error.
- Unsupported sort fields, unsupported sort orders, and unsupported filter values must be rejected clearly.
- Asset values must be validated so blank or malformed values cannot create unusable inventory records.
- Asset values must be normalized by trimming all values and lowercasing `domain` and `subdomain` values before storage, duplicate checks, and filtering.
- Duplicate create requests within the same organization must be rejected with a structured `409 Conflict` response.
- Assets with multiple tags must be discoverable by a single requested tag.
- `value_contains` searches must not return assets from another organization.
- Updates must not allow clients to change asset ownership.
- Create and update payloads containing `organization_id` must be rejected with a validation error.
- Missing, deleted, archived, or cross-organization assets must produce predictable domain errors; hard-deleted assets must return the asset-not-found response.
- Authentication failures, role failures, and asset-not-found failures must not leak another organization's data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide authenticated asset create, list, detail, update, and hard delete operations.
- **FR-002**: System MUST derive asset ownership from the authenticated user's organization context for every asset create, read, update, list, and delete operation.
- **FR-003**: System MUST reject asset create or update requests that include organization ownership supplied by clients.
- **FR-004**: System MUST allow viewer, analyst, and admin users to list and read assets owned by their organization.
- **FR-005**: System MUST allow analyst and admin users to create assets owned by their organization.
- **FR-006**: System MUST allow analyst and admin users to update assets owned by their organization.
- **FR-007**: System MUST allow only admin users to hard delete assets owned by their organization.
- **FR-008**: System MUST reject unauthenticated asset operations.
- **FR-009**: System MUST reject forbidden asset operations with a consistent structured error response.
- **FR-010**: System MUST report missing or cross-organization assets with a consistent structured not-found error response.
- **FR-011**: Structured domain errors MUST use the shape `{ "error": { "code": "...", "message": "...", "details": {} } }`.
- **FR-012**: Asset not-found errors MUST use the stable code `ASSET_NOT_FOUND`.
- **FR-013**: Forbidden asset action errors MUST use a stable authorization error code and human-readable message.
- **FR-014**: System MUST validate asset type against the supported values established by Phase 2: domain, subdomain, ip_address, service, certificate, and technology.
- **FR-015**: System MUST validate asset status against the supported values established by Phase 2: active, stale, and archived.
- **FR-016**: System MUST validate asset value so empty values are rejected.
- **FR-016a**: System MUST trim all asset values and lowercase `domain` and `subdomain` values before storage, duplicate checks, and filtering.
- **FR-017**: System MUST preserve organization-scoped uniqueness for asset type and value.
- **FR-017a**: System MUST reject duplicate asset create requests within the same organization with HTTP `409 Conflict` and a structured domain error.
- **FR-018**: Asset list responses MUST support filtering by type.
- **FR-019**: Asset list responses MUST support filtering by status.
- **FR-020**: Asset list responses MUST support filtering by tag.
- **FR-021**: Asset list responses MUST support filtering by source.
- **FR-022**: Asset list responses MUST support filtering by partial asset value using `value_contains`.
- **FR-023**: Asset list responses MUST support sorting by value, type, status, first_seen, last_seen, and created_at.
- **FR-024**: Asset list responses MUST support ascending and descending sort order.
- **FR-025**: Asset list responses MUST support pagination using page and page size.
- **FR-026**: Asset list pagination MUST default to page 1 and page size 20 when the client does not provide pagination parameters.
- **FR-027**: Asset list pagination MUST enforce a maximum page size of 100.
- **FR-027a**: Asset list pagination MUST reject `page < 1`, `page_size < 1`, and `page_size > 100` with validation errors.
- **FR-028**: Paginated asset list responses MUST include the returned items and enough pagination metadata for clients to understand the current page, page size, total results, and page availability.
- **FR-029**: Empty filtered lists MUST return a successful paginated response with an empty items collection.
- **FR-030**: System MUST reject unsupported filters, unsupported sort fields, unsupported sort orders, and invalid pagination parameters with clear validation errors.
- **FR-031**: System MUST keep all asset list, detail, update, and delete queries scoped to the authenticated user's organization.
- **FR-032**: System MUST include readable API documentation grouping, summaries, request models, response models, and documented error responses for all Phase 3 asset routes.
- **FR-033**: System MUST include tests for asset CRUD, filtering, sorting, pagination, validation, structured errors, RBAC, and tenant isolation.
- **FR-034**: System MUST update README notes if Phase 3 changes how users should create, query, update, delete, or test assets.
- **FR-035**: System MUST document any new required environment variables in `.env.example`.

### Key Entities

- **Asset**: An organization-owned attack-surface inventory item with type, value, status, first-seen timestamp, last-seen timestamp, source, tags, metadata, creation timestamp, and update timestamp.
- **Asset Filter**: A client-supplied list constraint for type, status, tag, source, or partial value matching that must be applied only inside the authenticated organization.
- **Asset Sort**: A client-supplied ordering preference using an allowed asset field and ascending or descending direction.
- **Paginated Asset Result**: A list response containing asset items and pagination metadata such as current page, page size, total result count, and page availability.
- **Structured Domain Error**: A stable error response for domain failures such as missing assets and forbidden actions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Phase 3 asset create, list, detail, update, and hard delete tests pass for the roles allowed to perform each action.
- **SC-002**: 100% of unauthorized or unauthenticated Phase 3 asset operation tests are rejected.
- **SC-003**: 100% of tenant isolation tests confirm users cannot list, read, update, delete, or infer assets owned by another organization.
- **SC-004**: Asset create and update payload tests confirm client-supplied organization ownership is rejected with a validation error.
- **SC-005**: Filtering tests cover type, status, tag, source, and value_contains and return only matching organization-owned assets.
- **SC-006**: Sorting tests cover every supported sort field and both sort orders.
- **SC-007**: Pagination tests verify default page 1, default page size 20, maximum page size 100, empty result behavior, and validation errors for `page < 1`, `page_size < 1`, and `page_size > 100`.
- **SC-008**: Validation tests reject unsupported asset types, unsupported asset statuses, empty asset values, unsupported sort options, and invalid pagination parameters.
- **SC-008b**: Asset value normalization tests verify values are trimmed for all types and `domain` and `subdomain` values are lowercased before duplicate checks and filtering.
- **SC-008a**: Duplicate create tests verify that matching organization, type, and value requests return structured `409 Conflict` without creating or updating a second asset.
- **SC-009**: Missing and cross-organization asset references return a structured not-found response with code `ASSET_NOT_FOUND`.
- **SC-010**: Forbidden asset actions return a structured forbidden response with a stable code and message.
- **SC-011**: Generated API documentation presents all Phase 3 asset routes under a readable asset grouping with clear summaries and response information.
- **SC-012**: A developer or evaluator can use documented Phase 3 instructions to authenticate as seeded users and exercise asset CRUD and list queries without needing public registration or organization creation.

## Assumptions

- Phase 1 has already established the backend application foundation, database connectivity, migration workflow, tests, Docker setup, and README setup notes.
- Phase 2 has already established organizations, users, assets, refresh tokens, seeded users, JWT authentication, current-user context, tenant scoping rules, asset type and status constraints, and role-based permissions.
- Public user registration, public organization creation, membership management, organization switching, bulk import, lifecycle re-sighting rules, relationship APIs, graph retrieval, rate limiting, caching, CI expansion, and LangChain analysis are outside Phase 3 unless referenced only as dependencies or future consumers.
- Delete behavior for Phase 3 is hard delete: `DELETE /assets/{asset_id}` permanently removes the asset from storage, and later reads return `ASSET_NOT_FOUND`.
- Cross-organization asset access is reported as not found to avoid leaking whether another tenant's asset exists.
- Asset list pagination uses page 1, page size 20, and maximum page size 100 unless a later clarification changes these values.
