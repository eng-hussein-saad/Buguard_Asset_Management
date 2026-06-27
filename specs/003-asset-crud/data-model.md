# Data Model: Asset CRUD

## Asset

Represents an organization-owned attack-surface inventory item.

**Fields**

- `id`: UUID primary key
- `organization_id`: required foreign key to organizations, derived from the
  authenticated user and never accepted from clients
- `type`: one of `domain`, `subdomain`, `ip_address`, `service`,
  `certificate`, `technology`
- `value`: non-empty canonical asset value; all values are trimmed, and
  `domain`/`subdomain` values are lowercased
- `status`: one of `active`, `stale`, `archived`
- `first_seen`: timezone-aware timestamp; defaults to current time when omitted
- `last_seen`: timezone-aware timestamp; defaults to current time when omitted
- `source`: nullable source string
- `tags`: list of tag strings
- `metadata`: JSON object exposed as `metadata` in API schemas and stored in the
  existing `metadata` column
- `created_at`: timezone-aware creation timestamp
- `updated_at`: timezone-aware update timestamp

**Relationships**

- Belongs to one organization
- May be referenced later by asset relationships in the same organization

**Validation and constraints**

- Unique by `(organization_id, type, value)`.
- Create and update payloads must reject `organization_id`.
- `value` must not be blank after trimming.
- `domain` and `subdomain` values are lowercased before duplicate checks,
  storage, filtering, and response serialization.
- Cross-organization detail, update, and delete attempts return the same
  structured not-found response as missing assets.
- Hard delete permanently removes the row in Phase 3.

## Asset Create Request

Represents client input for creating one asset.

**Fields**

- `type`: required supported asset type
- `value`: required non-blank value
- `status`: optional supported asset status, default `active`
- `first_seen`: optional timezone-aware timestamp
- `last_seen`: optional timezone-aware timestamp
- `source`: optional string
- `tags`: optional list of strings, default empty list
- `metadata`: optional JSON object, default empty object

**Validation and constraints**

- Extra fields are rejected, including `organization_id`.
- Values are normalized before uniqueness checks.
- Duplicate create within the authenticated organization returns HTTP 409 with a
  structured error.

## Asset Update Request

Represents editable asset details for an existing organization-owned asset.

**Fields**

- `type`: optional supported asset type
- `value`: optional non-blank value
- `status`: optional supported asset status
- `first_seen`: optional timezone-aware timestamp
- `last_seen`: optional timezone-aware timestamp
- `source`: optional nullable string
- `tags`: optional list of strings
- `metadata`: optional JSON object

**Validation and constraints**

- Extra fields are rejected, including `organization_id`.
- Empty update bodies are rejected with a validation error.
- If `type` or `value` changes, the normalized `(organization_id, type, value)`
  tuple must remain unique.
- Updates never change ownership.

## Asset Filter

Represents list constraints applied inside the authenticated organization.

**Fields**

- `type`: optional supported asset type
- `status`: optional supported asset status
- `tag`: optional tag string; matches assets containing that tag
- `source`: optional source string
- `value_contains`: optional non-empty partial value search

**Validation and constraints**

- Unsupported filter values are rejected.
- `value_contains` is trimmed and lowercased for `domain`/`subdomain` searches
  when paired with those types.
- Filters must never remove organization scoping.

## Asset Sort

Represents list ordering.

**Fields**

- `sort_by`: one of `value`, `type`, `status`, `first_seen`, `last_seen`,
  `created_at`; default `created_at`
- `sort_order`: one of `asc`, `desc`; default `desc`

**Validation and constraints**

- Unsupported sort fields and sort orders are rejected with validation errors.
- Sorting applies only after organization scoping and filtering.

## Paginated Asset Result

Represents the asset list response.

**Fields**

- `items`: list of asset responses for the current page
- `page`: current page number
- `page_size`: requested page size
- `total`: total matching assets in the authenticated organization
- `total_pages`: total page count, `0` when `total` is `0`
- `has_next`: whether a later page exists
- `has_previous`: whether an earlier page exists

**Validation and constraints**

- Defaults are page `1` and page size `20`.
- `page < 1`, `page_size < 1`, and `page_size > 100` are rejected.
- Empty filtered lists return HTTP 200 with `items: []` and pagination metadata.

## Structured Domain Error

Represents predictable domain failure responses.

**Fields**

- `error.code`: stable machine-readable code
- `error.message`: human-readable message
- `error.details`: object with optional structured context

**Validation and constraints**

- Asset not found must use code `ASSET_NOT_FOUND`.
- Forbidden asset actions use the existing stable authorization code
  `authorization_failed`.
- Duplicate creates use a stable duplicate-asset code and HTTP 409.
