# Feature Specification: Bulk Import Lifecycle

**Feature Branch**: `[004-bulk-import-lifecycle]`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 4 ONLY."

## Clarifications

### Session 2026-06-27

- Q: For Phase 4, how should mark-stale be exposed? -> A: Use existing PATCH /assets/{asset_id} with status=stale.
- Q: What timestamp contract should Phase 4 imports use for setting and refreshing first_seen / last_seen? -> A: Ignore client timestamps and use server processing time.
- Q: How should Phase 4 handle an imported asset that already exists with status=archived? -> A: Reactivate only when the import record explicitly sets status=active.
- Q: What HTTP status behavior should POST /assets/import use when records fail but the batch request itself is well-formed? -> A: Return 207 Multi-Status for partial failures and 422 when all records fail.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import Assets Idempotently (Priority: P1)

As an analyst or admin, I need to import a batch of observed assets without creating duplicates, so repeated imports from the same dataset keep the organization's inventory accurate.

**Why this priority**: Bulk import is the main Phase 4 workflow and the foundation for asset inventory ingestion. If imports create duplicates, later lifecycle and relationship behavior becomes unreliable.

**Independent Test**: Authenticate as an analyst or admin, import a dataset with valid assets, import the same dataset again, and verify the asset count does not increase while import results report existing assets as updated.

**Acceptance Scenarios**:

1. **Given** an analyst is authenticated and submits valid assets that do not exist in their organization, **When** the batch is imported, **Then** the assets are created under the analyst's organization with first-seen, last-seen, status, tags, metadata, and source values recorded.
2. **Given** an analyst imports the same valid dataset twice, **When** the second import completes, **Then** no duplicate assets are created and the summary reports the re-sighted assets as updated.
3. **Given** two organizations import assets with the same type and value, **When** each organization's users inspect their inventory, **Then** each organization has an independent asset record and neither import changes the other organization's data.

---

### User Story 2 - Refresh Existing Asset Observations (Priority: P1)

As an analyst or admin, I need re-imported assets to update their observation history and descriptive details, so the inventory reflects the most recent sighting while preserving original discovery history.

**Why this priority**: Phase 4 exists to make the inventory lifecycle-aware rather than simply append-only. Re-sightings must preserve truth about first discovery and update the current observation state.

**Independent Test**: Create or import an asset, re-import it later with new tags and updated metadata, then verify first-seen is preserved, last-seen changes to the server processing time of the accepted re-sighting, tags are merged without duplicates, metadata is merged predictably, and stale assets become active again.

**Acceptance Scenarios**:

1. **Given** an existing active asset has a first-seen timestamp, tags, and metadata, **When** it is imported again with new observation details, **Then** first-seen remains unchanged, last-seen is refreshed to the server processing time of the accepted re-sighting, tags are combined without duplicates, and metadata is merged using a predictable strategy.
2. **Given** an existing stale asset is observed in a new import, **When** the import completes, **Then** the asset becomes active again and the import summary counts it as updated.
3. **Given** an existing archived asset appears in an import record without `status=active`, **When** the import completes, **Then** the asset remains archived while accepted non-status fields are merged and the summary counts it as updated.
4. **Given** an existing archived asset appears in an import record with `status=active`, **When** the import completes, **Then** the asset becomes active and the summary counts it as updated.
5. **Given** an import record has metadata keys that already exist on the asset, **When** the import completes, **Then** the newer import values replace conflicting keys while non-conflicting existing metadata remains available.

---

### User Story 3 - Report Partial Import Failures (Priority: P1)

As an API consumer, I need malformed import records to be reported without failing the entire batch, so usable observations are still saved and bad records can be corrected.

**Why this priority**: Real ingestion data is often imperfect. A single bad record must not block the organization from importing the rest of an otherwise useful dataset.

**Independent Test**: Submit a batch containing valid records and malformed records, then verify valid records are created or updated, invalid records are reported by input position with clear reasons, and the request returns a summary with HTTP 207 Multi-Status. Submit a well-formed batch where every record is malformed, then verify no assets are changed and the request returns the same summary shape with HTTP 422.

**Acceptance Scenarios**:

1. **Given** a batch contains valid records and records missing required values, **When** the batch is imported, **Then** valid records are processed, malformed records are included in the error list with their original positions, and the response uses HTTP 207 Multi-Status.
2. **Given** a batch contains unsupported asset types, unsupported statuses, blank values, or malformed tag and metadata shapes, **When** the batch is imported, **Then** those records are rejected individually and do not prevent other valid records from being processed.
3. **Given** every record in a well-formed batch is malformed, **When** the import completes, **Then** no assets are created or updated and the response reports all failures in a stable summary shape with HTTP 422.

---

### User Story 4 - Mark Assets Stale Through Asset Update (Priority: P2)

As an analyst or admin, I need to mark assets as stale when they are no longer observed, so the inventory distinguishes current observations from historical findings without deleting useful context.

**Why this priority**: Lifecycle handling requires an explicit way to move previously observed assets out of the active set before future imports can reactivate them.

**Independent Test**: Authenticate as an analyst or admin, update an organization-owned active asset through `PATCH /assets/{asset_id}` with `status=stale`, verify viewers can see the new stale status, verify viewers cannot perform the status update, and verify importing the stale asset again returns it to active status.

**Acceptance Scenarios**:

1. **Given** an analyst owns an active asset in their organization, **When** they update it through `PATCH /assets/{asset_id}` with `status=stale`, **Then** the asset status changes to stale and remains visible in organization-scoped asset reads.
2. **Given** a viewer attempts to update an asset status to stale, **When** the request is processed, **Then** the action is rejected with a structured forbidden error.
3. **Given** a user references an asset owned by another organization, **When** they attempt to update its status to stale, **Then** the system responds as if the asset is unavailable to that user.

### Edge Cases

- Importing the same dataset multiple times must not increase the number of assets in the organization.
- Import records must never accept or trust client-supplied organization ownership.
- Matching for existing assets must use the authenticated organization, asset type, and canonical asset value.
- Canonical asset value handling must stay consistent with Phase 3 value normalization.
- Duplicate records within the same import batch must be treated as one created asset followed by re-sightings, not as duplicate assets.
- Tags from existing assets and import records must be merged without duplicates.
- Metadata conflicts must be resolved predictably by keeping existing non-conflicting keys and letting the newest import value replace a conflicting key.
- A stale asset that appears in an import must become active again.
- Archived assets that appear in an import must be reactivated only when the import record explicitly sets `status=active`.
- Malformed records must include their input index and a human-readable reason in the import summary.
- Very large batches must return a bounded, readable summary and must not leak assets across organizations.
- An import where all records fail must not create or update any assets and must return the stable import summary shape with HTTP 422.
- A mixed import with at least one accepted record and at least one failed record must return the stable import summary shape with HTTP 207 Multi-Status.
- Authentication failures, role failures, missing assets, malformed records, and cross-organization references must not reveal another organization's data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an authenticated bulk asset import operation for organization-owned assets.
- **FR-002**: System MUST allow analyst and admin users to import assets for their organization.
- **FR-003**: System MUST reject viewer and unauthenticated bulk import attempts with structured authorization or authentication errors.
- **FR-004**: System MUST derive asset ownership for every imported record from the authenticated user's organization context.
- **FR-005**: System MUST reject or ignore any import field that attempts to provide organization ownership from client input, and imported assets MUST remain scoped to the authenticated organization.
- **FR-006**: System MUST match existing assets by authenticated organization, asset type, and canonical asset value.
- **FR-007**: System MUST create a new asset when an imported asset does not already exist in the authenticated organization.
- **FR-008**: Newly imported assets MUST record first-seen and last-seen using server processing time, plus status, source, tags, and metadata when those values are supplied or defaulted by the import contract.
- **FR-009**: System MUST NOT create duplicate assets when the same dataset is imported more than once.
- **FR-010**: System MUST NOT create duplicate assets when the same asset appears multiple times in one import batch.
- **FR-011**: Re-importing an existing asset MUST preserve the asset's original first-seen timestamp.
- **FR-012**: Re-importing an existing asset MUST update the asset's last-seen timestamp to the server processing time of the latest accepted sighting.
- **FR-013**: Re-importing an existing asset MUST merge tags without duplicate tag values.
- **FR-014**: Re-importing an existing asset MUST merge metadata predictably by preserving non-conflicting existing keys and replacing conflicting keys with the newest import value.
- **FR-015**: Re-importing a stale asset MUST change its status to active.
- **FR-016**: Re-importing an archived asset MUST keep it archived unless the import record explicitly sets `status=active`.
- **FR-017**: Re-importing an archived asset with explicit `status=active` MUST reactivate it.
- **FR-018**: System MUST support marking an organization-owned asset as stale through `PATCH /assets/{asset_id}` with `status=stale`.
- **FR-019**: System MUST allow analyst and admin users to update organization-owned assets to stale.
- **FR-020**: System MUST reject viewer and unauthenticated attempts to update asset status to stale.
- **FR-021**: Stale status update behavior MUST only affect assets owned by the authenticated user's organization.
- **FR-022**: Missing or cross-organization assets referenced by stale status update behavior MUST return the structured asset-not-found response established in Phase 3.
- **FR-023**: Bulk import MUST continue processing valid records when other records in the same batch are malformed.
- **FR-024**: Bulk import responses MUST include counts for created, updated, and failed records.
- **FR-025**: Bulk import responses MUST include an error list for failed records with the original input index and a clear reason.
- **FR-026**: Bulk import MUST return HTTP 207 Multi-Status when a well-formed batch has at least one accepted record and at least one failed record.
- **FR-027**: Bulk import MUST return HTTP 422 when a well-formed batch has no accepted records because every record fails validation.
- **FR-028**: Bulk import MUST return the same stable import summary shape for successful, partial-failure, and all-record-failure outcomes.
- **FR-029**: System MUST validate imported asset type using the supported asset types established by earlier phases.
- **FR-030**: System MUST validate imported asset status using the supported lifecycle statuses active, stale, and archived.
- **FR-031**: System MUST reject import records with missing, blank, or malformed asset values.
- **FR-032**: System MUST reject malformed tags, metadata, or other import fields for the affected record without crashing the entire batch.
- **FR-033**: System MUST ignore any client-supplied first-seen or last-seen fields in import records and MUST use server processing time for lifecycle timestamps. Other client-supplied timestamp fields MUST be rejected as unsupported import fields.
- **FR-034**: Import behavior MUST keep all reads, writes, duplicate checks, and lifecycle updates scoped to the authenticated organization.
- **FR-035**: Structured domain errors MUST use the established shape `{ "error": { "code": "...", "message": "...", "details": {} } }` for domain failures outside per-record import errors.
- **FR-036**: System MUST include tests for idempotent import, duplicate records within one batch, metadata merge behavior, tag merge behavior, malformed records, partial-failure and all-record-failure HTTP statuses, stale reactivation, archived asset import behavior, stale status update permissions, server-time lifecycle timestamps, and tenant isolation.
- **FR-037**: System MUST update README notes if Phase 4 changes how evaluators import assets, interpret import summaries, or exercise lifecycle behavior.
- **FR-038**: System MUST document any new required environment variables in `.env.example`.

### Key Entities

- **Import Batch**: A submitted collection of asset observation records that must be processed under one authenticated organization and summarized after processing.
- **Import Record**: A single asset observation containing asset type, value, optional status, source, tags, and metadata; lifecycle timestamps are assigned by the server during processing.
- **Import Summary**: The result of a batch import, including created, updated, and failed counts plus per-record failure details.
- **Import Error**: A validation or processing failure tied to a specific input record index and a clear reason.
- **Asset Lifecycle State**: The status that communicates whether an asset is active, stale, or archived.
- **Asset Observation History**: The first-seen and last-seen values that preserve when an asset was first and most recently observed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Phase 4 import tests confirm importing the same dataset twice does not increase the organization's asset count.
- **SC-002**: 100% of import ownership tests confirm client-supplied organization ownership cannot create, update, or affect assets outside the authenticated organization.
- **SC-003**: 100% of re-import tests confirm first-seen is preserved and last-seen changes to server processing time for accepted re-sightings.
- **SC-004**: 100% of tag merge tests confirm duplicate tag values are not introduced.
- **SC-005**: 100% of metadata merge tests confirm non-conflicting keys are preserved and conflicting keys use the newest import value.
- **SC-006**: 100% of malformed-record tests confirm valid records still process and failed records are reported with index and reason.
- **SC-007**: 100% of stale lifecycle tests confirm stale assets become active when imported again.
- **SC-008**: 100% of archived lifecycle tests confirm archived assets remain archived unless an import record explicitly sets `status=active`.
- **SC-009**: 100% of stale status update tests confirm analyst and admin users can update organization-owned assets to stale and viewers cannot.
- **SC-010**: 100% of cross-organization import and stale status update tests confirm one organization cannot affect another organization's assets.
- **SC-011**: 100% of partial-failure tests confirm mixed accepted and failed records return HTTP 207 Multi-Status with a stable import summary.
- **SC-012**: 100% of all-record-failure tests confirm a well-formed batch with no accepted records returns HTTP 422 with the same stable import summary shape.
- **SC-013**: Import summaries consistently include created, updated, failed, and errors fields for successful, partially failed, and fully failed batches.
- **SC-014**: A developer or evaluator can use documented Phase 4 instructions to authenticate as seeded users, import a sample dataset, re-import it, inspect the summary, and verify lifecycle behavior without public registration or organization creation.

## Assumptions

- Phase 1 has already established the backend application foundation, database connectivity, migration workflow, tests, Docker setup, and README setup notes.
- Phase 2 has already established organizations, users, assets, seeded users, JWT authentication, current-user context, tenant scoping rules, supported asset statuses, and role-based permissions.
- Phase 3 has already established tenant-scoped asset CRUD, asset value normalization, structured domain errors, validation behavior, and the asset-not-found response.
- Phase 4 is limited to bulk import, deduplication, lifecycle handling, import edge cases, and marking assets stale. Relationship APIs, graph retrieval, rate limiting, caching, CI expansion, and LangChain analysis remain outside this phase.
- The mark-stale capability is exposed through existing asset update behavior using `PATCH /assets/{asset_id}` with `status=stale`.
- Import metadata merge behavior uses shallow key-level merging unless a later clarification explicitly requires nested merge semantics.
- Import lifecycle timestamps are controlled by the server: client-supplied first-seen and last-seen fields are ignored, other client-supplied timestamp fields are rejected as unsupported import fields, newly created assets use server processing time for first-seen and last-seen, and accepted re-sightings preserve first-seen while refreshing last-seen to server processing time.
