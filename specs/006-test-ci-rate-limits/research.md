# Research: Test CI Rate Limits

## Decision: Use GitHub Actions for continuous quality checks

**Rationale**: The project already uses uv, pytest, ruff, and mypy-compatible
configuration in `pyproject.toml`. GitHub Actions is the repository-native CI
surface requested by the feature and can install from the locked dependency set,
run linting, run tests, and optionally run type checks on pushes and pull
requests.

**Alternatives considered**: A local-only script was rejected because Phase 6
requires checks on pushed or proposed changes. A different CI provider was
rejected because no alternate provider configuration exists in the repository.

## Decision: Add focused tests around the existing Phase 1-5 surfaces

**Rationale**: The repository already has contract, integration, and unit test
directories covering health, auth, seed data, assets, import lifecycle, RBAC,
tenant isolation, relationships, graphs, and security helpers. Extending those
locations keeps tests discoverable and preserves the current pytest
configuration.

**Alternatives considered**: Rebuilding the suite into a new test hierarchy was
rejected because it would add churn without improving Phase 6 behavior.

## Decision: Implement rate limits as reusable service checks at API boundaries

**Rationale**: Login, refresh, and bulk import are abuse-prone entry points and
must be rejected before additional expensive work. A reusable rate-limit service
can centralize keys, thresholds, windows, retry metadata, and structured 429
responses while route handlers decide the operation and effective caller.

**Alternatives considered**: Per-route ad hoc counters were rejected because
they would duplicate window math and make the later AI analysis limit harder to
adopt consistently. Database-backed counters were rejected because rate limits
are transient operational state and would add write load to the primary store.

## Decision: Use effective caller identities from trusted context

**Rationale**: The clarified spec requires login limits by attempted username
plus client network identity, and refresh/import limits by authenticated user
plus authenticated organization. These identities do not rely on
client-supplied tenant ownership and align with the constitution.

**Alternatives considered**: IP-only limits were rejected because they can
block unrelated users behind a shared network. Payload `organization_id` was
rejected because clients must not control tenant identity.

## Decision: Return structured 429 errors for rate-limit violations

**Rationale**: Existing API behavior uses structured domain errors for invalid,
missing, forbidden, duplicate, and malformed operations. Rate-limit failures
should use the same error envelope with a stable code and message so clients
and tests can recognize them.

**Alternatives considered**: Plain-text or framework-default 429 responses were
rejected because they would break the project-wide structured error behavior.

## Decision: Cache only organization-scoped asset list and graph reads

**Rationale**: The spec requires caching for asset list and graph reads only.
Both responses are tenant-owned, read-heavy, and already have clear inputs:
authenticated organization, list query parameters, or graph center asset id.
Keeping the cache surface small limits invalidation risk.

**Alternatives considered**: Caching every asset read was rejected because the
feature does not require it. Global graph cache keys were rejected because they
would create tenant leakage risk.

## Decision: Invalidate broad organization asset/graph cache namespaces after writes

**Rationale**: Asset list filters and graph neighborhoods can be affected by
asset create/refresh, update, delete/archive, bulk import, relationship create
or delete, and stale status changes. Organization-scoped namespace invalidation
is simpler and safer than trying to compute every affected list filter or graph
key.

**Alternatives considered**: Fine-grained invalidation of only one list or one
graph key was rejected because tags, metadata, status, relationship edges, and
pagination can affect many cached responses. Time-only expiry was rejected
because the spec requires freshness after writes.

## Decision: Treat cache service unavailability as graceful fallback

**Rationale**: The constitution requires optional services to degrade
gracefully. If Redis or the configured cache is unavailable, asset list and
graph reads should execute normal organization-scoped database queries and
return correct uncached responses. Writes should not fail solely because
invalidation could not reach the cache service.

**Alternatives considered**: Failing reads or writes when cache is unavailable
was rejected because it would make caching a hard dependency and conflict with
Phase 6 fallback requirements.

## Decision: Document AI analysis rate limit without implementing AI analysis

**Rationale**: Phase 6 explicitly excludes AI analysis behavior but requires a
future policy of 5 attempts per minute. Capturing that policy in docs and
configuration comments prepares Phase 7 without expanding scope.

**Alternatives considered**: Adding a placeholder AI endpoint was rejected
because the feature specification forbids AI analysis behavior in Phase 6.
