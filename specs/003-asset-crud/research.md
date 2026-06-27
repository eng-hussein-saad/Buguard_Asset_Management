# Research: Asset CRUD

## Decision: Keep Phase 3 as direct CRUD, not import lifecycle behavior

**Rationale**: The Phase 3 section of `PLAN.md` is limited to direct asset
create, list, detail, update, delete, filtering, sorting, pagination, validation,
structured errors, tenant scoping, and OpenAPI polish. Bulk import,
deduplication merge behavior, stale reactivation, and partial import failures
are explicitly Phase 4 concerns.

**Alternatives considered**: Implementing tag/metadata merge and re-sighting in
Phase 3 was rejected because it would blur acceptance criteria and duplicate the
future import service responsibilities.

## Decision: Derive asset ownership from `get_current_user`

**Rationale**: The constitution and Phase 2 auth design require tenant-owned
resources to derive organization scope from authenticated context. The existing
`get_current_user` dependency validates JWT claims against the database user and
returns the user's `organization_id` and `role`.

**Alternatives considered**: Accepting `organization_id` in create/update
payloads was rejected because it violates tenant isolation and the Phase 3 spec.

## Decision: Extend existing RBAC permissions

**Rationale**: Phase 2 already defines `READ_ASSETS`, `CREATE_ASSET`,
`UPDATE_ASSET`, and `DELETE_OR_ARCHIVE`. Phase 3 can reuse those permissions:
viewer/analyst/admin for reads, analyst/admin for create/update, and admin only
for hard delete.

**Alternatives considered**: Route-local role checks were rejected because they
would duplicate the existing `services.rbac` policy table.

## Decision: Normalize asset values in the service layer

**Rationale**: Normalization must occur before storage, duplicate checks, and
filtering. Keeping the logic in `tenant_assets` makes it reusable by routes,
repositories, and future Phase 4 import behavior while leaving persistence
methods simple.

**Alternatives considered**: Normalizing only with Pydantic validators was
rejected because repository/service callers in future phases may bypass API
schemas. Database-generated normalization was rejected because rules differ by
asset type and should be testable in Python.

## Decision: Use Pydantic v2 models for validation and OpenAPI documentation

**Rationale**: The project already uses FastAPI and Pydantic v2 for request and
response contracts. Schemas can reject extra fields, including
`organization_id`, validate enum values, enforce pagination bounds, and produce
clear OpenAPI docs.

**Alternatives considered**: Manual validation inside route functions was
rejected because it would scatter rules and reduce generated documentation
quality.

## Decision: Implement structured domain errors through `AppError`

**Rationale**: Existing project errors already return
`{ "error": { "code": "...", "message": "...", "details": {} } }`. Phase 3
should add asset-specific not-found and duplicate errors while preserving the
same envelope.

**Alternatives considered**: Raw `HTTPException` detail strings were rejected
because the spec requires structured errors with stable codes.

## Decision: Use repository-level filtered count plus paginated query

**Rationale**: The list endpoint must return items plus pagination metadata,
including total result count and page availability. A scoped count query and a
scoped item query keep the behavior predictable and make empty result sets a
successful response.

**Alternatives considered**: Returning only `limit`/`offset` results without a
count was rejected because it would not satisfy the required pagination
metadata.

## Decision: Map database uniqueness violations to HTTP 409

**Rationale**: Assets are unique by `(organization_id, type, value)`. The service
should check for duplicates before create for clear errors, and still map
database `IntegrityError` to a structured 409 to handle races.

**Alternatives considered**: Letting PostgreSQL errors surface as 500 responses
was rejected because duplicate creates are expected domain failures.
