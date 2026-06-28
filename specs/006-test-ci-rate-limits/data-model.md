# Data Model: Test CI Rate Limits

## Automated Test Suite

Collection of repeatable checks that validates application health,
authentication, tenant isolation, RBAC, asset workflows, imports,
relationships, graphs, structured errors, rate limits, cache behavior, and CI
readiness.

### Fields

- `scope`: string. Test category such as health, auth, assets, imports,
  relationships, graph, rate_limit, cache, or ci.
- `location`: path. Test module or workflow location.
- `covered_requirements`: array of spec requirement ids.
- `expected_result`: pass, fail for intentional negative fixture, or skipped
  with explicit reason.

### Validation Rules

- Tests must be runnable through the documented pytest command sequence.
- Tests must include admin, analyst, viewer, and second-organization seeded
  users.
- Tests must cover both allowed and forbidden behavior for tenant isolation and
  RBAC-sensitive operations.
- Intentional CI-failure validation must not leave broken committed code.

## Continuous Quality Workflow

Repository workflow that installs dependencies and runs quality checks on
changes.

### Fields

- `trigger`: push and pull_request.
- `dependency_install`: locked uv dependency installation.
- `checks`: linting, automated tests, and type checks where supported.
- `status`: pass or fail.
- `failure_visibility`: failing step name and logs visible to maintainers.

### Validation Rules

- Workflow must fail if linting fails.
- Workflow must fail if tests fail.
- Workflow should run static typing when current project configuration supports
  it without blocking unrelated Phase 6 delivery.
- Workflow must not require public registration or organization creation.

## Rate Limit Rule

Threshold and identity rule for an abuse-prone operation.

### Fields

- `operation`: enum. `login`, `refresh`, `bulk_import`, or future
  `ai_analysis`.
- `limit`: integer. Maximum accepted attempts in the window.
- `window_seconds`: integer. Phase 6 uses 60 seconds.
- `effective_caller`: string. Trusted identity used to count attempts.
- `storage_key`: string. Internal key derived from operation, window, and
  effective caller.
- `rejection`: structured 429 error payload.

### Validation Rules

- Login allows no more than 5 attempts per minute per attempted username plus
  client network identity.
- Refresh allows no more than 10 attempts per minute per authenticated user
  plus authenticated organization.
- Bulk import allows no more than 10 attempts per minute per authenticated user
  plus authenticated organization.
- Future AI analysis is documented at no more than 5 attempts per minute, but
  no endpoint is implemented in Phase 6.
- Effective caller identity must not use client-supplied organization ownership.
- Requests below thresholds must continue normal behavior.

### State Transitions

- `available`: request count is below or equal to the threshold and operation
  may continue.
- `limited`: threshold has been exceeded during the active window and the
  operation returns a structured 429 response before additional work.
- `reset`: window expires and a new request starts a new count.

## Rate-Limit Violation

Structured rejection returned when a rate-limited operation exceeds its
threshold.

### Fields

- `status_code`: integer. Always 429.
- `code`: string. Stable machine code such as `rate_limited`.
- `message`: string. Human-readable rate-limit explanation.
- `operation`: string. Operation that was limited.
- `retry_after_seconds`: integer. Remaining window duration when available.

### Validation Rules

- Response must use the project structured error shape.
- Login, refresh, and import violations must be covered by automated tests.
- Bulk import violation must occur before additional import processing.

## Cache Entry

Stored read result for an organization-scoped asset list or graph response.

### Fields

- `cache_type`: enum. `asset_list` or `asset_graph`.
- `organization_id`: UUID. Required. Derived from authenticated user.
- `input_hash`: string. Stable representation of response-affecting inputs.
- `payload`: serialized response body.
- `created_at`: timestamp.
- `expires_at`: timestamp or cache TTL.
- `namespace_version`: string or integer used for broad organization
  invalidation.

### Validation Rules

- Cache key must include authenticated organization.
- Asset list cache key must include all user-visible query inputs that affect
  response: filters, sort field, sort order, page, and page size.
- Graph cache key must include authenticated organization and center asset id.
- Cache entries must never be shared across organizations.
- Cache reads must fall back to uncached database queries if the cache service
  is unavailable, corrupt, or returns invalid data.

### State Transitions

- `miss`: no usable entry exists; service queries the database and may store
  the result.
- `hit`: usable entry exists under the authenticated organization and matching
  inputs; service returns the cached payload.
- `invalidated`: relevant write changes the organization namespace so prior
  entries are no longer served.
- `fallback`: cache service is unavailable; service returns correct uncached
  data.

## Cache Invalidation Event

Write-side event that marks organization-scoped asset list and graph cache
entries stale.

### Fields

- `organization_id`: UUID. Authenticated organization affected by the write.
- `reason`: enum. asset_create_refresh, asset_update, asset_delete_archive,
  bulk_import, relationship_create, relationship_delete, mark_stale.
- `occurred_at`: timestamp.
- `affected_cache_types`: asset_list, asset_graph, or both.

### Validation Rules

- Invalidation must run after asset create or refresh.
- Invalidation must run after asset update, delete, or archive.
- Invalidation must run after bulk import, including partial success.
- Invalidation must run after relationship create or delete.
- Invalidation must run after marking assets stale.
- Invalidation failure caused by cache unavailability must not leak data or
  fail otherwise successful database writes.
