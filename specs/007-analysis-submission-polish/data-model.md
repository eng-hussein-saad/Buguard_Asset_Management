# Data Model: Analysis Submission Polish

## Analysis Report

Generated response for an authenticated inventory risk report.

**Fields**

- `summary`: concise natural-language summary grounded only in selected evidence.
- `risks`: ordered list of `Risk Entry` values.
- `evidence_asset_ids`: list of selected asset IDs used by the report.
- `status`: `completed`, `no_data`, `unavailable`, or `failed`.
- `message`: human-readable status detail for no-data, unavailable, or failure cases.
- `generated_at`: server timestamp for completed reports.

**Validation rules**

- Evidence IDs must be selected from assets in the authenticated user's
  organization.
- Completed reports must not reference asset IDs outside `evidence_asset_ids`.
- No-data responses return an empty evidence list and no fabricated risks.
- Unavailable/failure responses must not include secrets or partial invented
  reports.

## Analysis Filter

User-visible selection criteria for report input assets.

**Fields**

- `type`: optional asset type filter.
- `status`: optional asset status filter.
- `tag`: optional tag filter.
- `source`: optional source filter.
- `value_contains`: optional value substring filter.
- `certificate_lifecycle_status`: optional lifecycle filter for certificate assets.
- `limit`: bounded maximum number of assets selected for provider input.

**Validation rules**

- Organization scope is never accepted from request input.
- Text filters are trimmed and cannot be blank.
- Limits must be bounded to a documented maximum.

## Evidence Asset

Existing asset selected from the authenticated organization for analysis.

**Fields**

- `id`: internal asset UUID.
- `type`: asset type.
- `value`: normalized asset value.
- `status`: asset lifecycle status.
- `source`: optional source.
- `tags`: tag list.
- `metadata`: metadata object, including `expires` for certificates when present.
- `certificate_lifecycle_status`: derived status for certificate assets.

**Validation rules**

- Must belong to the authenticated user's organization.
- Must match all requested report filters.
- Certificate lifecycle status is derived, not stored as source of truth.

## Risk Entry

Report item describing a potential issue.

**Fields**

- `title`: short risk name.
- `severity`: `low`, `medium`, `high`, or `critical`.
- `description`: concise explanation.
- `evidence_asset_ids`: one or more asset IDs when the risk refers to specific assets.

**Validation rules**

- Asset-specific risks must include evidence asset IDs.
- All evidence asset IDs must be in the selected evidence set.
- Certificate lifecycle findings must include the relevant certificate asset IDs.

## Certificate Lifecycle Date

Raw expiry value stored at `asset.metadata.expires` for certificate assets.

**Fields**

- `raw_value`: original metadata value.
- `parsed_date`: parsed calendar date when valid.
- `parse_error`: reason when missing, malformed, or unparseable.

**Validation rules**

- Raw value remains in `metadata.expires`.
- Malformed values are reported during import but do not invalidate unrelated
  valid records.

## Certificate Lifecycle Status

Derived value computed from `metadata.expires`.

**Values**

- `expired`: expiry date is earlier than the evaluation date.
- `expiring_soon`: expiry date is from the evaluation date through the next 30
  calendar days, inclusive.
- `valid`: expiry date is after the expiring-soon window.
- `unknown`: expiry is missing, malformed, or unparseable.

**Relationships**

- Derived from certificate `Asset` metadata.
- Included in asset read/list responses for certificates.
- Available in certificate lifecycle filters.
- Included in graph nodes for certificates.
- Used by analysis report input and certificate lifecycle risk generation.

## Sample Import Record

Evaluator dataset item accepted by bulk import.

**Fields**

- `id`: optional import-local external reference.
- `type`: asset type such as `domain`, `subdomain`, or `certificate`.
- `value`: asset value.
- `status`: optional asset status.
- `source`: optional source.
- `tags`: tag list.
- `metadata`: metadata object.
- `parent`: optional import-local ID reference for subdomain-to-domain relation.
- `covers`: optional import-local ID reference for certificate-to-subdomain relation.

**Validation rules**

- `organization_id` is not accepted.
- `id` is import-local and not persisted as ownership or primary identity.
- Valid assets are created or refreshed with existing lifecycle semantics.
- Unsupported, malformed, or incomplete records are reported per record.
- Larger datasets use the same accepted record shape.

## Import Relationship Reference

Import-local relationship request derived from `parent` or `covers`.

**Fields**

- `record_id`: import-local source record ID.
- `target_record_id`: import-local target record ID.
- `relationship_type`: `parent` or `covers`.
- `status`: `created`, `already_exists`, or `failed`.
- `reason`: failure detail for unresolved references.

**Validation rules**

- References resolve only within the same authenticated import batch.
- Source and target records must both be valid and processed in the authenticated
  organization.
- Missing, invalid, skipped, ambiguous, or unsafe references are reported without
  creating relationships.

## Parent Relationship

Relationship from a subdomain asset to its parent domain asset.

**Fields**

- `source_asset_id`: subdomain asset ID.
- `target_asset_id`: domain asset ID.
- `relationship_type`: `parent`.
- `metadata`: optional relationship metadata.

**Validation rules**

- Source and target must belong to the authenticated organization.
- Duplicate relationship handling follows existing relationship semantics.

## Covers Relationship

Relationship from a certificate asset to the subdomain asset it covers.

**Fields**

- `source_asset_id`: certificate asset ID.
- `target_asset_id`: subdomain asset ID.
- `relationship_type`: `covers`.
- `metadata`: optional relationship metadata.

**Validation rules**

- Source and target must belong to the authenticated organization.
- Graph responses expose certificate lifecycle status for certificate nodes.

## Final Submission Checklist

Documentation-backed readiness artifact.

**Fields**

- `setup_steps`: clean checkout and environment setup.
- `seeded_credentials`: local evaluator users and roles.
- `workflow_examples`: authentication, import, asset filters, relationships,
  graph, lifecycle, rate limits, and analysis.
- `verification_commands`: tests and linting.
- `scope_assumptions`: no public registration, no public organization creation,
  single-organization users, authenticated organization scoping, no live
  scanning, future multi-organization support.
- `known_tradeoffs`: remaining limitations and future improvements.
