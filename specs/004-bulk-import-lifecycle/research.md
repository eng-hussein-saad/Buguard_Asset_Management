# Phase 4 Research: Bulk Import Lifecycle

## Decision: Keep Phase 4 import on the existing assets route

**Rationale**: The Phase 3 assets API already owns asset authentication,
structured errors, RBAC, schemas, and OpenAPI documentation. Adding
`POST /assets/import` to `app/api/routes/assets.py` keeps the public API grouped
around asset operations and allows reuse of `get_db`, `get_current_user`, and
the existing `ERROR_RESPONSES` pattern.

**Alternatives considered**: A separate import router was considered, but it
would add a second asset-facing route module before the API surface requires
that split.

## Decision: Implement import orchestration in `tenant_assets`

**Rationale**: Phase 3 already centralizes asset permissions, normalization,
duplicate handling, not-found behavior, and response conversion in
`app/services/tenant_assets.py`. Import behavior depends on those same
invariants plus lifecycle rules, so keeping the orchestration in the same
service reduces risk of bypassing tenant or RBAC checks.

**Alternatives considered**: A new `asset_imports.py` service was considered.
It may become useful if import logic grows substantially, but Phase 4 can remain
cohesive inside the existing tenant asset service.

## Decision: Match existing assets by organization, type, and canonical value

**Rationale**: The `assets` table already enforces
`UNIQUE (organization_id, type, value)`, and Phase 3 normalizes domain-like
values before duplicate checks. Import must use the same normalization and
lookup strategy to make repeated imports idempotent and tenant-scoped.

**Alternatives considered**: Matching by raw input value was rejected because it
would conflict with Phase 3 normalization and allow duplicate domain-like assets
that differ only by casing or surrounding whitespace.

## Decision: Use server processing time for lifecycle timestamps

**Rationale**: The spec explicitly rejects client-supplied first-seen,
last-seen, observed-at, or equivalent timestamp fields. Using one server-side
timestamp per accepted record gives deterministic lifecycle behavior, prevents
clients from rewriting observation history, and keeps first-seen preservation
simple.

**Alternatives considered**: Accepting client observation timestamps was
rejected by clarification and would make trust, validation, and ordering rules
more complex.

## Decision: Merge tags as an ordered de-duplicated union

**Rationale**: Existing tags should remain available and new observations
should add missing values without duplicates. Preserving existing tag order and
appending new unique import tags gives stable results while keeping behavior
easy to test.

**Alternatives considered**: Replacing all tags on import was rejected because
re-sightings should enrich the asset rather than erase prior context.

## Decision: Merge metadata shallowly with newest conflicts winning

**Rationale**: The spec states that non-conflicting keys remain available and
conflicting keys use the newest import value. A shallow key-level merge is
predictable, easy to document, and matches the assumption in the specification.

**Alternatives considered**: Deep recursive merge was rejected because nested
conflict rules were not requested and would complicate record-level validation.

## Decision: Return 207 for mixed accepted and failed records, 422 when all fail

**Rationale**: Phase 4 needs to save valid records even when other records in
the same well-formed batch are malformed. HTTP 207 distinguishes partial
success from full success, while HTTP 422 communicates that a syntactically
well-formed import request contained no valid records to process.

**Alternatives considered**: Always returning 200 for any processed batch was
rejected because it hides correction-needed failures. Failing the entire batch
on the first malformed record was rejected because the spec requires per-record
failure reporting.

## Decision: Keep request-level failures in the structured error envelope

**Rationale**: Authentication failures, authorization failures, malformed JSON,
and invalid batch shapes are not per-record import failures. They should use the
project-wide structured domain error conventions already documented for Phase 3.

**Alternatives considered**: Returning import summary shapes for authentication
or authorization failures was rejected because it would blur request-level
failures with per-record validation results.

## Decision: No new environment variables are required

**Rationale**: Phase 4 uses the existing database, authentication, RBAC, and
asset model. No external provider, cache, queue, or rate limiter is introduced
in this phase.

**Alternatives considered**: Queue-backed asynchronous imports were deferred
because Phase 4 scope is evaluator-scale synchronous API behavior.
