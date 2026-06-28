# Feature Specification: Test CI Rate Limits

**Feature Branch**: `[006-test-ci-rate-limits]`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 6 ONLY."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Core Asset Management Behavior (Priority: P1)

As a developer or evaluator, I need comprehensive automated tests for the asset management workflows, so I can trust that authentication, tenant isolation, RBAC, asset lifecycle, imports, relationships, and graph behavior remain correct as the project evolves.

**Why this priority**: Phase 6 is primarily a reliability phase. The core assessment logic is security-sensitive and must be protected by repeatable tests before additional operational features can be trusted.

**Independent Test**: Run the automated test suite from a clean project setup and verify that tests cover health checks, seeded authentication, refresh tokens, RBAC, tenant isolation, asset CRUD, filtering, sorting, pagination, bulk import, deduplication, lifecycle handling, relationships, graph retrieval, and structured errors.

**Acceptance Scenarios**:

1. **Given** the project is set up with seeded users and test data support, **When** the automated tests run, **Then** the suite validates successful and forbidden paths for viewer, analyst, and admin roles.
2. **Given** two organizations have overlapping asset values, **When** tenant isolation tests run, **Then** users from one organization cannot read, update, import, relate, graph, or infer another organization's assets.
3. **Given** import and lifecycle tests include duplicate, malformed, stale, archived, tag, and metadata cases, **When** the tests run, **Then** the expected summaries, status changes, and merge behavior are verified.

---

### User Story 2 - Run Continuous Quality Checks (Priority: P1)

As a maintainer, I need automated quality checks to run for repository changes, so regressions are caught before they reach the main branch.

**Why this priority**: Local tests are useful only when consistently enforced. Continuous checks provide the project-level reliability expected for production-minded backend work.

**Independent Test**: Open a change that intentionally breaks formatting, linting, or a test, and verify the continuous quality workflow fails; then fix the issue and verify the workflow passes.

**Acceptance Scenarios**:

1. **Given** a change is pushed or proposed for review, **When** continuous quality checks start, **Then** dependency setup, linting, and tests run automatically.
2. **Given** any required quality check fails, **When** the workflow completes, **Then** the overall result is failed and the failing step is visible to the maintainer.
3. **Given** all required quality checks pass, **When** the workflow completes, **Then** the change is reported as passing.

---

### User Story 3 - Rate Limit Abuse-Prone Operations (Priority: P1)

As an organization user, I need sensitive and expensive operations to be rate-limited, so credential abuse, token abuse, and excessive imports are slowed without blocking normal usage.

**Why this priority**: Login, refresh, and import operations are high-risk entry points. Rate limiting improves security and operational stability without changing the main asset workflows.

**Independent Test**: Repeatedly call each rate-limited operation above its allowed threshold and verify that the system returns a structured rate-limit response while normal requests under the threshold continue to work.

**Acceptance Scenarios**:

1. **Given** repeated login attempts exceed the allowed threshold, **When** another login request is made during the rate-limit window, **Then** the request is rejected with a structured rate-limit response.
2. **Given** repeated token refresh attempts exceed the allowed threshold, **When** another refresh request is made during the rate-limit window, **Then** the request is rejected with a structured rate-limit response.
3. **Given** repeated bulk import attempts exceed the allowed threshold, **When** another import request is made during the rate-limit window, **Then** the request is rejected before additional import work is processed.

---

### User Story 4 - Cache Organization-Scoped Reads Safely (Priority: P2)

As an organization user, I need any cached read results to remain isolated to my organization and fresh after writes, so caching cannot leak or serve stale asset data across tenants.

**Why this priority**: Caching is required in Phase 6 and touches tenant-owned reads, so it must follow the constitution's tenant isolation rules.

**Independent Test**: Read assets or a graph for two organizations with overlapping values, mutate one organization's data, and verify cached responses never include another organization's data and are refreshed after relevant writes.

**Acceptance Scenarios**:

1. **Given** two organizations request cacheable asset or graph reads, **When** cached results are stored and returned, **Then** each cached result is scoped to the authenticated organization.
2. **Given** an asset or relationship changes after a cached read, **When** the same organization reads the affected asset list or graph again, **Then** the response reflects the change rather than stale cached data.
3. **Given** the cache service is temporarily unavailable, **When** users read assets or graphs, **Then** the system continues to serve correct organization-scoped results without leaking stale or cross-tenant cached data.

---

### User Story 5 - Document Verification and Operational Behavior (Priority: P3)

As an evaluator, I need clear notes for running tests, understanding continuous checks, and recognizing rate-limited behavior, so I can verify Phase 6 without reverse-engineering the project.

**Why this priority**: Documentation makes the reliability work visible and reproducible, but it depends on the tests, quality checks, and rate limiting being defined first.

**Independent Test**: Follow the project documentation from a clean checkout to run tests, identify the continuous quality workflow, authenticate as seeded users, and observe rate-limited responses for protected operations.

**Acceptance Scenarios**:

1. **Given** an evaluator reads the project documentation, **When** they follow the test instructions, **Then** they can run the automated checks locally.
2. **Given** an evaluator reviews the documented rate limits, **When** they exercise login, refresh, and import behavior, **Then** the observed limits match the documented expectations.
3. **Given** Phase 6 includes caching, **When** an evaluator reads the documentation, **Then** they can understand its tenant-scoping, invalidation, and graceful fallback behavior.

### Edge Cases

- Tests must include seeded-user authentication for admin, analyst, viewer, and a second organization user.
- Tests must verify that viewer users can read allowed organization-owned resources but cannot perform analyst or admin mutations.
- Tests must verify that analyst users can create or refresh asset observations, update assets, import assets, mark assets stale, and create relationships, while admin-only delete or archive behavior remains protected.
- Tests must verify that overlapping asset values across organizations stay independent.
- Tests must verify that missing or cross-organization assets are reported without exposing another organization's data.
- Tests must verify malformed import records, partial import failures, all-record import failures, duplicate records within one batch, repeated imports, metadata merge, tag merge, stale reactivation, and archived asset handling.
- Tests must verify relationship duplicate prevention, invalid relationship types, relationship listing, graph retrieval, and graph behavior for isolated assets.
- Rate limiting must apply to login, refresh, and bulk import operations without preventing normal usage below the documented thresholds.
- Rate-limit responses must use a consistent structured error shape.
- Rate-limit counters must not allow one organization or user to bypass limits by providing tenant ownership in request input.
- Future AI analysis behavior must inherit rate limiting when that endpoint is added in a later phase.
- Cached reads must include authenticated organization scope in cache identity.
- Cached reads must be invalidated after asset create or refresh, asset update, asset delete or archive, bulk import, relationship create or delete, and marking assets stale.
- Caching must degrade gracefully when the cache service is temporarily unavailable.
- Continuous quality checks must fail when required linting or tests fail.
- Documentation must not require public registration or public organization creation because users and organizations are seeded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include automated tests for the health check and application startup behavior.
- **FR-002**: System MUST include automated tests for the seed workflow and seeded-user authentication.
- **FR-003**: System MUST include automated tests for login, refresh token behavior, logout where present, and invalid credential handling.
- **FR-004**: System MUST include automated tests for viewer, analyst, and admin role permissions across protected operations.
- **FR-005**: System MUST include automated tests proving all tenant-owned reads and writes are scoped to the authenticated user's organization.
- **FR-006**: System MUST include automated tests for asset creation or refresh, asset reads, asset updates, asset deletion or archival where supported, filtering, sorting, and pagination.
- **FR-007**: System MUST include automated tests for bulk import success, repeated import deduplication, duplicate records within one import, malformed records, partial failures, all-record failures, metadata merge, tag merge, stale reactivation, and archived asset handling.
- **FR-008**: System MUST include automated tests for relationship creation, duplicate prevention, relationship listing, graph retrieval, graph retrieval for isolated assets, invalid relationship payloads, and cross-tenant relationship blocking.
- **FR-009**: System MUST include automated tests confirming structured errors for authentication failures, authorization failures, missing resources, invalid input, duplicate relationships, malformed imports, and rate-limit violations.
- **FR-010**: Automated tests MUST be runnable locally with one documented command sequence from a clean checkout.
- **FR-011**: System MUST provide a continuous quality workflow that runs on pushed changes and proposed changes.
- **FR-012**: Continuous quality checks MUST install project dependencies from the locked dependency set before running required checks.
- **FR-013**: Continuous quality checks MUST run linting and the automated test suite.
- **FR-014**: Continuous quality checks SHOULD run static type checks when the project configuration supports them without blocking unrelated Phase 6 delivery.
- **FR-015**: Continuous quality checks MUST fail the overall workflow when linting or tests fail.
- **FR-016**: System MUST rate limit login attempts to no more than 5 attempts per minute per effective caller.
- **FR-017**: System MUST rate limit refresh attempts to no more than 10 attempts per minute per effective caller.
- **FR-018**: System MUST rate limit bulk import attempts to no more than 10 attempts per minute per effective caller.
- **FR-019**: System MUST define rate limiting so the later AI analysis endpoint can be limited to no more than 5 attempts per minute when that endpoint is implemented.
- **FR-020**: Rate-limited requests MUST return a structured error response that clearly communicates the request was rate-limited.
- **FR-021**: Rate limiting MUST NOT accept or trust client-supplied organization ownership for tenant or caller identity.
- **FR-022**: Rate limiting MUST continue to allow normal authenticated and unauthenticated behavior below the documented thresholds.
- **FR-023**: System MUST cache organization-scoped asset listing and organization-scoped asset graph retrieval.
- **FR-024**: Cache identity MUST include the authenticated organization and all user-visible query inputs that affect the response.
- **FR-025**: Cached results MUST never be shared across organizations.
- **FR-026**: Cached asset and graph reads MUST be invalidated after asset create or refresh, asset update, asset delete or archive, bulk import, relationship create or delete, and marking assets stale.
- **FR-027**: System MUST continue to return correct uncached responses when caching is temporarily unavailable.
- **FR-028**: System MUST update project documentation with local test commands, continuous quality check behavior, rate limits, caching behavior, cache invalidation behavior, and cache fallback behavior added in this phase.
- **FR-029**: System MUST document any new required environment variables in `.env.example`.
- **FR-030**: Phase 6 MUST NOT add public user registration, public organization creation, organization switching, or AI analysis behavior.

### Key Entities

- **Automated Test Suite**: The collection of repeatable checks that validates application health, authentication, tenant isolation, RBAC, asset workflows, imports, relationships, graphs, structured errors, and rate limiting.
- **Seeded Test User**: A predefined user assigned to one organization and one role, used for local and automated verification without public registration.
- **Continuous Quality Workflow**: The repository-level process that installs dependencies, runs linting, runs tests, and reports pass or fail status on pushed and proposed changes.
- **Rate Limit Rule**: A threshold for an abuse-prone operation, including the protected operation, allowed request count, time window, caller identity, and structured rejection behavior.
- **Rate-Limit Violation**: A rejected request caused by exceeding a rate limit within the active time window.
- **Cache Entry**: A stored read result for an organization-scoped asset list or graph response, identified by organization scope and request inputs and invalidated after relevant writes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of required automated tests pass locally before Phase 6 is considered complete.
- **SC-002**: 100% of continuous quality workflow runs execute required linting and automated tests on pushed and proposed changes.
- **SC-003**: 100% of intentionally failing test or lint changes cause the continuous quality workflow to fail.
- **SC-004**: 100% of seeded-user authentication tests confirm admin, analyst, viewer, and second-organization users can be used for verification.
- **SC-005**: 100% of tenant isolation tests confirm users cannot access, mutate, relate, graph, import into, or infer assets outside their organization.
- **SC-006**: 100% of RBAC tests confirm viewer, analyst, and admin permissions match the role model defined for the project.
- **SC-007**: 100% of import and lifecycle tests confirm deduplication, filtering of malformed records, partial failure reporting, all-record failure reporting, metadata merge, tag merge, stale reactivation, and archived asset behavior.
- **SC-008**: 100% of relationship and graph tests confirm duplicate prevention, organization scoping, graph response shape, and isolated asset graph behavior.
- **SC-009**: 100% of login rate-limit tests confirm more than 5 attempts per minute per effective caller are rejected with a structured rate-limit response.
- **SC-010**: 100% of refresh rate-limit tests confirm more than 10 attempts per minute per effective caller are rejected with a structured rate-limit response.
- **SC-011**: 100% of bulk import rate-limit tests confirm more than 10 attempts per minute per effective caller are rejected before additional import work is processed.
- **SC-012**: 100% of cache isolation tests confirm cached reads never return another organization's asset list, graph nodes, or graph edges.
- **SC-013**: 100% of cache invalidation tests confirm affected cached reads are refreshed after relevant asset, import, relationship, and stale-status changes.
- **SC-014**: A developer or evaluator can follow the documentation to run local tests, understand continuous quality checks, exercise seeded authentication, and recognize rate-limited responses without public registration or organization creation.

## Assumptions

- Phase 1 has already established the backend application foundation, database connectivity, migration workflow, basic tests, Docker setup, and README setup notes.
- Phase 2 has already established organizations, users, seeded users, JWT authentication, refresh tokens, current-user context, tenant scoping rules, and role-based permissions.
- Phase 3 has already established tenant-scoped asset CRUD, filtering, sorting, pagination, value normalization, validation behavior, and structured domain errors.
- Phase 4 has already established idempotent asset observation behavior, bulk import, lifecycle handling, import summaries, and organization-scoped asset ingestion.
- Phase 5 has already established asset relationships, relationship listing, graph retrieval, duplicate relationship prevention, and simple graph visualization behavior.
- Phase 6 is limited to comprehensive automated tests, continuous quality checks, rate limiting, required organization-scoped caching, and related documentation.
- Caching is required for Phase 6 completion, with cache keys scoped by authenticated organization and invalidation after relevant asset, import, relationship, and stale-status changes.
- The future AI analysis endpoint is outside Phase 6 scope, but its expected rate-limit policy is documented so Phase 7 can adopt it consistently.
