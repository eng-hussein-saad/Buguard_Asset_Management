# Phase 4 Data Model: Bulk Import Lifecycle

## Import Batch

Represents one authenticated request to import asset observations for the
current user's organization.

**Fields**

- `items`: Non-empty list of import records.

**Validation Rules**

- Request must be authenticated.
- Current user must have analyst or admin import permission.
- Client input must not provide or control `organization_id`.
- Batch-level malformed JSON or missing `items` fails as a request-level
  validation error.
- Record-level validation failures are collected in the import summary when the
  batch shape itself is valid.

**Relationships**

- Processed under exactly one organization from authenticated user context.
- Contains many import records.
- Produces exactly one import summary.

## Import Record

Represents one asset observation inside a batch.

**Fields**

- `type`: Required asset type. Supported values are `domain`, `subdomain`,
  `ip_address`, `service`, `certificate`, and `technology`.
- `value`: Required asset value. Trimmed and canonicalized with the same
  Phase 3 normalization used by asset CRUD.
- `status`: Optional lifecycle status. Supported values are `active`, `stale`,
  and `archived`; default for new assets is `active`.
- `source`: Optional source string describing where the observation came from.
- `tags`: Optional list of tag strings.
- `metadata`: Optional shallow JSON object for observation details.

**Ignored Client Fields**

- `organization_id`
- `first_seen`
- `last_seen`
- `observed_at`
- Any equivalent client timestamp field used to control lifecycle timestamps

**Validation Rules**

- Missing or blank `value` fails only that record.
- Unsupported `type` fails only that record.
- Unsupported `status` fails only that record.
- Malformed `tags`, `metadata`, or other import fields fail only that record.
- Valid records are processed even when other records fail.

## Asset Lifecycle State

Reuses the existing `Asset.status` values.

**Values**

- `active`: Asset is currently observed.
- `stale`: Asset was previously observed but is no longer current.
- `archived`: Asset is removed from active operational use.

**State Transitions**

- New imported asset uses explicit import `status` when valid, otherwise
  defaults to `active`.
- Existing `active` asset remains or becomes the import record's explicit valid
  status when supplied.
- Existing `stale` asset becomes `active` on any accepted re-sighting.
- Existing `archived` asset remains `archived` unless the import record
  explicitly sets `status=active`.
- Existing `archived` asset with explicit `status=active` becomes `active`.
- `PATCH /assets/{asset_id}` with `status=stale` marks an organization-owned
  active asset stale when requested by analyst/admin users.

## Asset Observation History

Reuses existing `Asset.first_seen` and `Asset.last_seen` fields.

**Rules**

- New imported assets set both `first_seen` and `last_seen` to server
  processing time.
- Re-imported assets preserve existing `first_seen`.
- Re-imported assets set `last_seen` to server processing time for the accepted
  record.
- Client-supplied lifecycle timestamps are ignored.

## Tag Merge

Represents the combined tags after a re-sighting.

**Rules**

- Existing tags are preserved.
- Import tags are appended only when not already present.
- Duplicate tag values are not introduced.
- New assets store the de-duplicated import tags.

## Metadata Merge

Represents the shallow JSON merge after a re-sighting.

**Rules**

- Existing non-conflicting keys remain available.
- Import metadata replaces existing values for conflicting keys.
- Import metadata adds new keys.
- Nested objects are treated as values at the top-level key unless future specs
  explicitly require recursive merge behavior.

## Import Summary

Represents the stable response shape for successful, partially failed, and
fully failed well-formed import batches.

**Fields**

- `created`: Count of records that created new assets.
- `updated`: Count of records that updated existing assets, including duplicate
  records within the same batch after the first successful create.
- `failed`: Count of records rejected during per-record validation or
  processing.
- `errors`: List of import errors.

**Status Mapping**

- HTTP 200 when all records are accepted.
- HTTP 207 Multi-Status when at least one record is accepted and at least one
  record fails.
- HTTP 422 when no records are accepted because every record fails.

## Import Error

Represents a per-record failure in an otherwise well-formed batch.

**Fields**

- `index`: Zero-based position of the original input record.
- `reason`: Human-readable explanation of the record failure.

**Rules**

- Errors must not reveal assets or organization data from another tenant.
- Errors must remain stable enough for API consumers to correct failed records.

## Repository Access Pattern

Phase 4 uses the existing `assets` table and does not require a new database
table.

**Required Helpers**

- Organization-scoped lookup by `organization_id`, `type`, and canonical
  `value`.
- Organization-scoped create using server-owned timestamps.
- Existing asset update that can change status, last-seen, source, tags, and
  metadata without changing ownership.

**Indexes and Constraints**

- Existing `UNIQUE (organization_id, type, value)` remains the authoritative
  duplicate guard.
- Existing organization/type/value lookup index supports import deduplication.
