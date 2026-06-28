# Data Model: Asset Relationships Graph

## Asset Relationship

Represents a typed directed connection between two assets in one organization.

### Fields

- `id`: UUID primary key.
- `organization_id`: UUID. Required. Derived from the authenticated user's
  organization and never accepted from client input.
- `source_asset_id`: UUID. Required. Must reference an asset in the same
  organization.
- `target_asset_id`: UUID. Required. Must reference an asset in the same
  organization.
- `relationship_type`: string enum. Required. One of `belongs_to`,
  `resolves_to`, `runs_on`, `covers`, or `detected_on`.
- `metadata`: object. Optional relationship metadata. Defaults to `{}`.
- `created_at`: server-owned timestamp.

### Validation Rules

- Source asset must exist in the authenticated user's organization.
- Target asset must exist in the authenticated user's organization.
- Client-supplied `organization_id` is rejected or ignored before persistence.
- Duplicate relationships with the same organization, source, target, and type
  are rejected with a structured duplicate conflict.
- Blank, malformed, non-underscore, or unsupported relationship types are
  rejected with the structured error envelope.
- Viewer users may read relationships but may not create them.

### Relationships

- Belongs to one organization.
- References one source asset.
- References one target asset.

## Relationship Type

Canonical semantic label for an asset relationship.

### Allowed Values

- `belongs_to`
- `resolves_to`
- `runs_on`
- `covers`
- `detected_on`

### Validation Rules

- Values are lowercase underscore machine values only.
- Unsupported values fail request validation or service validation before any
  relationship is created.

## Graph Center

The selected organization-owned asset around which the graph response is built.

### Fields

- `id`: UUID of the selected asset.
- `type`: asset type.
- `value`: asset value.
- `label`: display label derived from asset value.

### Validation Rules

- Center asset must belong to the authenticated user's organization.
- Missing or cross-organization center assets return the established
  asset-not-found response.

## Graph Node

Visualization-friendly representation of an organization-owned asset included
in the graph response.

### Fields

- `id`: UUID.
- `type`: asset type.
- `value`: asset value.
- `label`: display label derived from asset value.

### Validation Rules

- The center asset is always included in `nodes`, including when there are no
  relationships.
- Nodes are unique by asset id.
- Nodes are limited to the center asset and directly connected assets in
  Phase 5.
- Nodes from other organizations are never included.

## Graph Edge

Visualization-friendly representation of an organization-owned relationship.

### Fields

- `id`: UUID of the relationship.
- `source_asset_id`: UUID.
- `target_asset_id`: UUID.
- `relationship_type`: canonical relationship type.
- `label`: display label derived from `relationship_type`.

### Validation Rules

- Edge source and target ids must both resolve to organization-owned graph
  nodes.
- Edges are unique by relationship id.
- Edges are limited to relationships where the center asset is either the
  source or target.
- Edges from other organizations are never included.

## Graph Response

Response returned by `GET /assets/{asset_id}/graph`.

### Fields

- `center`: Graph Center.
- `nodes`: array of Graph Node.
- `edges`: array of Graph Edge.

### State Rules

- Connected center asset: includes center, directly related nodes, and directly
  connected edges.
- Isolated center asset: includes center in `center`, includes the same asset in
  `nodes`, and returns an empty `edges` array.
- Missing or cross-tenant center asset: returns structured asset-not-found and
  no graph payload.

## Graph View

Simple visual surface used to confirm graph behavior.

### Fields and Inputs

- `asset_id`: UUID selected or supplied by the user.
- Graph payload loaded from `GET /assets/{asset_id}/graph`.
- Error payload loaded from the same endpoint when graph retrieval fails.

### Validation Rules

- The view must use the graph endpoint as its source of truth.
- The view must not independently traverse relationships or implement tenant
  filtering.
- The view labels nodes by asset value and edges by relationship type.
