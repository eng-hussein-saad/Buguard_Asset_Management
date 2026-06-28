# Research: Asset Relationships Graph

## Decision: Keep relationships in the existing asset API boundary

**Rationale**: Phase 5 is centered on assets and their graph neighborhood. The
existing app already exposes asset operations through `app/api/routes/assets.py`
and keeps asset behavior in `app/schemas/assets.py`,
`app/services/tenant_assets.py`, and repository modules. Placing relationship
creation, listing, graph retrieval, and the simple graph view near the asset
API keeps authorization, structured errors, and tenant scoping consistent.

**Alternatives considered**: A standalone `relationships` router was considered,
but it would add another API boundary without changing ownership. It can be
introduced later if relationship behavior becomes large enough to justify it.

## Decision: Derive relationship ownership only from authenticated context

**Rationale**: The constitution requires tenant-owned resources to derive
`organization_id` from the authenticated user. Relationship creation touches two
asset ids, so both source and target assets must be loaded through
organization-scoped asset queries before a relationship is created.

**Alternatives considered**: Accepting `organization_id` in the payload was
rejected because it would create a cross-tenant spoofing path and conflicts
with earlier asset and import behavior.

## Decision: Use a unique relationship key and structured duplicate conflict

**Rationale**: The model already defines a uniqueness rule for
`organization_id`, `source_asset_id`, `target_asset_id`, and
`relationship_type`. The service should pre-check duplicates where practical
and also translate database `IntegrityError` into the project error envelope
with a conflict status, so concurrent duplicate attempts remain safe.

**Alternatives considered**: Returning the existing relationship as a successful
idempotent response was rejected because the clarified specification requires a
structured duplicate error and no additional record.

## Decision: Use the canonical `RelationshipType` enum values

**Rationale**: `belongs_to`, `resolves_to`, `runs_on`, `covers`, and
`detected_on` are already represented in the model enum and match the
clarified spec. Pydantic schemas should validate against these values before
service logic runs.

**Alternatives considered**: Free-form relationship labels were rejected
because graph consumers need stable labels and the spec requires unsupported,
blank, malformed, or non-underscore values to fail.

## Decision: Return one-hop graph data from a backend service

**Rationale**: Phase 5 is explicitly limited to the center asset, directly
connected assets, and directly connected relationships. The backend service can
enforce this with bounded organization-scoped adjacency queries and produce a
visualization-friendly response containing `center`, `nodes`, and `edges`.

**Alternatives considered**: Recursive traversal and full connected-component
graphs were rejected as outside Phase 5 scope. Client-side traversal was
rejected because the visualization must not duplicate tenant-scoping or graph
business rules.

## Decision: Keep graph visualization simple and endpoint-driven

**Rationale**: The visualization is a required demonstration aid, not a second
source of graph rules. It should accept or use an asset id, call
`GET /assets/{asset_id}/graph`, render labels from the returned asset values
and relationship types, and display structured error states as returned.

**Alternatives considered**: A rich interactive graph editor was rejected as
outside Phase 5. A static mock was rejected because the success criteria require
loading data from the graph endpoint.

## Decision: No new environment variables are planned

**Rationale**: Relationships, graph retrieval, and the simple visualization can
run on the existing FastAPI, database, auth, seed, and asset configuration.

**Alternatives considered**: Adding a graph rendering service or cache was
rejected because Phase 5 does not require external graph infrastructure.
