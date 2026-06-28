# Feature Specification: Asset Relationships Graph

**Feature Branch**: `[005-asset-relationships-graph]`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 5 ONLY."

## Clarifications

### Session 2026-06-28

- Q: How should duplicate relationship creation attempts behave? -> A: Return a structured duplicate error, such as `409 Conflict`, and do not create a duplicate.
- Q: What canonical format should relationship type values use? -> A: Use underscore values: `belongs_to`, `resolves_to`, `runs_on`, `covers`, `detected_on`.
- Q: Should the graph response `nodes` collection include the center asset? -> A: Include the center asset in `nodes`, even when there are no edges.
- Q: What traversal depth should `GET /assets/{asset_id}/graph` support in Phase 5? -> A: One-hop only: center asset, directly connected assets, and directly connected relationships.
- Q: Should the optional graph visualization be included in Phase 5 scope or explicitly deferred? -> A: Make visualization required for Phase 5 completion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Tenant-Scoped Relationships (Priority: P1)

As an analyst or admin, I need to connect two assets in my organization with a typed relationship, so the inventory can represent how domains, subdomains, IP addresses, services, certificates, and technologies relate to each other.

**Why this priority**: Relationships are the foundation of Phase 5. Without safe relationship creation, the graph endpoint and visualization cannot provide trustworthy attack-surface context.

**Independent Test**: Authenticate as an analyst or admin, create two assets in the same organization, create a relationship between them, then verify the relationship is stored once under the authenticated organization and is visible to organization users.

**Acceptance Scenarios**:

1. **Given** an analyst is authenticated and both source and target assets belong to their organization, **When** they create a relationship with a supported relationship type, **Then** the relationship is created under the analyst's organization and references the selected source and target assets.
2. **Given** an admin is authenticated and both assets belong to their organization, **When** they create a relationship that already exists with the same source, target, and relationship type, **Then** the system prevents a duplicate relationship and returns a structured duplicate error without creating a second copy.
3. **Given** a viewer is authenticated, **When** they attempt to create a relationship, **Then** the action is rejected with a structured forbidden error.

---

### User Story 2 - Block Unsafe or Cross-Tenant Relationships (Priority: P1)

As an organization user, I need relationship creation to reject missing assets and cross-organization references, so one tenant cannot infer, connect, or alter another tenant's asset graph.

**Why this priority**: Tenant isolation is mandatory for this backend. Relationship creation touches two assets at once, making it a high-risk path for accidental cross-tenant leakage.

**Independent Test**: Authenticate as a user in one organization and attempt to create relationships that reference a missing asset, an asset from another organization, or one local asset plus one cross-organization asset; verify each request fails without exposing the other organization's data.

**Acceptance Scenarios**:

1. **Given** an analyst references a source asset that does not exist in their organization, **When** they create a relationship, **Then** the system responds as if the source asset is unavailable to that user.
2. **Given** an analyst references a target asset that belongs to another organization, **When** they create a relationship, **Then** the system rejects the request without revealing that the target asset exists elsewhere.
3. **Given** a relationship creation payload includes organization ownership, **When** the request is processed, **Then** the supplied ownership is ignored or rejected and the relationship scope is derived only from the authenticated user's organization.

---

### User Story 3 - Retrieve an Asset Relationship Graph (Priority: P1)

As a viewer, analyst, or admin, I need to retrieve the relationship graph around one asset, so I can understand nearby attack-surface context without manually following relationship records one by one.

**Why this priority**: The graph endpoint is the main read outcome for Phase 5 and the contract consumed by any visualization.

**Independent Test**: Create a small organization-owned asset graph, authenticate as a viewer in that organization, request the graph for the center asset, and verify the response contains the center, nodes, and edges for organization-owned relationships only.

**Acceptance Scenarios**:

1. **Given** a viewer is authenticated and requests the graph for an asset in their organization, **When** the graph is returned, **Then** the response includes the center asset, related nodes, and relationship edges in a visualization-friendly shape.
2. **Given** an organization has relationships connected to the selected asset, **When** a user requests that asset's graph, **Then** the response includes edges where the selected asset is either the source or target and includes the directly connected assets as nodes.
3. **Given** a user requests the graph for an asset owned by another organization, **When** the request is processed, **Then** the system responds as if the asset is unavailable to that user.

---

### User Story 4 - List Organization Relationships (Priority: P2)

As a viewer, analyst, or admin, I need to list relationships in my organization, so I can inspect graph data, verify imports or manual relationship creation, and support debugging without relying only on a single asset graph view.

**Why this priority**: Listing relationships makes the relationship model observable and testable, but it depends on safe relationship creation and graph retrieval first.

**Independent Test**: Authenticate as each role, list relationships after creating several organization-owned relationships, and verify only relationships from the authenticated user's organization are returned.

**Acceptance Scenarios**:

1. **Given** relationships exist in two organizations, **When** a user lists relationships, **Then** only relationships owned by the user's organization are returned.
2. **Given** a viewer lists relationships, **When** the request is processed, **Then** the viewer can read the relationships but cannot create new ones.
3. **Given** no relationships exist for the user's organization, **When** they list relationships, **Then** the response is successful and contains an empty collection.

---

### User Story 5 - View a Simple Graph Visualization (Priority: P3)

As an evaluator or developer, I want a simple graph view that uses the graph endpoint, so I can visually confirm relationships without duplicating graph logic outside the backend contract.

**Why this priority**: Visualization is useful for demonstration and evaluation, but depends on the required backend relationship and graph behavior being correct first.

**Independent Test**: Authenticate as a user with graph access, open the visualization for an organization-owned asset, and verify it fetches the graph endpoint and renders labeled nodes and edges from the returned data.

**Acceptance Scenarios**:

1. **Given** a user provides or selects an asset ID, **When** the graph view loads, **Then** it fetches the graph endpoint for that asset and displays nodes labeled by asset value.
2. **Given** graph edges are returned, **When** the graph view renders, **Then** the edges are labeled by relationship type.
3. **Given** the graph endpoint returns an error for the selected asset, **When** the graph view receives the response, **Then** it displays the structured error state without inventing graph data.

### Edge Cases

- Relationship creation must fail when the source asset is missing or unavailable to the authenticated organization.
- Relationship creation must fail when the target asset is missing or unavailable to the authenticated organization.
- Relationship creation must never accept or trust client-supplied organization ownership.
- Relationships must not connect assets from different organizations.
- Duplicate relationships with the same organization, source asset, target asset, and relationship type must not create additional records.
- Relationship type values use underscore machine values: `belongs_to`, `resolves_to`, `runs_on`, `covers`, and `detected_on`; unsupported or blank relationship types must be rejected.
- Relationship reads and graph retrieval must be available to viewers, analysts, and admins within the same organization.
- Relationship creation must be available only to analysts and admins.
- Missing and cross-organization assets must be reported without exposing whether another organization owns the referenced asset.
- Graph responses for assets with no relationships must include the center asset in both `center` and `nodes`, with an empty `edges` collection.
- Graph responses must avoid duplicate nodes and duplicate edges.
- Graph retrieval is limited to one hop around the selected asset in Phase 5.
- Graph retrieval must include organization scoping for every asset and relationship considered.
- Graph visualization must consume the graph endpoint instead of rebuilding graph traversal rules independently.
- Authentication failures, role failures, missing assets, duplicate relationships, malformed relationship payloads, and cross-organization references must use consistent structured error behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an authenticated operation to create an asset relationship between a source asset and a target asset.
- **FR-002**: System MUST allow analyst and admin users to create relationships for assets in their organization.
- **FR-003**: System MUST reject viewer and unauthenticated relationship creation attempts with structured authorization or authentication errors.
- **FR-004**: Relationship creation MUST derive relationship ownership from the authenticated user's organization context.
- **FR-005**: Relationship creation payloads MUST reject or ignore any field that attempts to provide organization ownership from client input.
- **FR-006**: Relationship creation MUST verify that the source asset exists in the authenticated user's organization.
- **FR-007**: Relationship creation MUST verify that the target asset exists in the authenticated user's organization.
- **FR-008**: Relationship creation MUST reject attempts to connect assets that are missing, unavailable, or not owned by the authenticated user's organization.
- **FR-009**: Relationship creation MUST store source asset, target asset, relationship type, optional metadata, and organization ownership for accepted relationships.
- **FR-010**: System MUST prevent duplicate relationships with the same organization, source asset, target asset, and relationship type.
- **FR-011**: Duplicate relationship attempts MUST NOT create additional relationship records.
- **FR-012**: System MUST validate relationship type so blank, malformed, non-underscore, or unsupported relationship types are rejected.
- **FR-013**: System MUST support the canonical relationship type values `belongs_to`, `resolves_to`, `runs_on`, `covers`, and `detected_on`.
- **FR-014**: System MUST provide an authenticated operation to list relationships in the current organization.
- **FR-015**: Relationship listing MUST return only relationships owned by the authenticated user's organization.
- **FR-016**: Viewer, analyst, and admin users MUST be able to read organization-owned relationships.
- **FR-017**: System MUST provide an authenticated graph retrieval operation centered on one asset.
- **FR-018**: Graph retrieval MUST verify the center asset belongs to the authenticated user's organization.
- **FR-019**: Graph retrieval MUST return a response with a center object, a nodes collection, and an edges collection.
- **FR-020**: The graph center object MUST include the selected asset's id, type, and value.
- **FR-021**: The graph nodes collection MUST include the center asset, even when the selected asset has no relationships.
- **FR-022**: Each graph node MUST include an asset id, asset type, and display label based on the asset value.
- **FR-023**: Each graph edge MUST include source asset id, target asset id, and relationship type.
- **FR-024**: Graph retrieval MUST include directly connected organization-owned relationships where the selected asset is either the source or target.
- **FR-025**: Graph retrieval MUST include only organization-owned nodes and edges.
- **FR-026**: Graph retrieval MUST be limited to one hop around the selected asset in Phase 5 and MUST NOT include second-hop or full connected-component traversal.
- **FR-027**: Graph retrieval MUST avoid duplicate nodes and duplicate edges in the response.
- **FR-028**: Graph retrieval for an organization-owned asset with no relationships MUST return the center asset in `center`, include the same asset in `nodes`, and return an empty `edges` collection.
- **FR-029**: Missing or cross-organization assets referenced by relationship creation or graph retrieval MUST return the structured asset-not-found response established by earlier phases.
- **FR-030**: Duplicate relationship attempts MUST return a structured duplicate error, such as `409 Conflict`, using the established error shape `{ "error": { "code": "...", "message": "...", "details": {} } }`, without creating an additional relationship record.
- **FR-031**: Invalid relationship type failures MUST use the established structured error shape `{ "error": { "code": "...", "message": "...", "details": {} } }`.
- **FR-032**: System MUST provide a simple graph visualization for Phase 5.
- **FR-033**: Graph visualization MUST accept or use an asset ID and fetch the graph retrieval operation for that asset.
- **FR-034**: Graph visualization MUST display graph nodes and edges from the graph response and label nodes by asset value and edges by relationship type.
- **FR-035**: Graph visualization MUST NOT duplicate backend graph traversal or tenant-scoping logic.
- **FR-036**: Graph visualization MUST display a readable error state when graph retrieval fails for the selected asset.
- **FR-037**: System MUST include tests for relationship creation, duplicate prevention, relationship listing, graph retrieval, RBAC, invalid relationship payloads, missing assets, cross-tenant blocking, and visualization route behavior.
- **FR-038**: System MUST update README notes if Phase 5 adds relationship examples, graph retrieval instructions, visualization usage, or evaluator-visible behavior.
- **FR-039**: System MUST document any new required environment variables in `.env.example`.

### Key Entities

- **Asset Relationship**: A typed connection between a source asset and a target asset within one organization, optionally carrying metadata about the relationship.
- **Relationship Type**: The semantic label for a connection, using canonical underscore values such as `belongs_to`, `resolves_to`, `runs_on`, `covers`, or `detected_on`.
- **Graph Center**: The selected organization-owned asset around which the graph response is built.
- **Graph Node**: A visualization-friendly representation of an organization-owned asset included in the graph response.
- **Graph Edge**: A visualization-friendly representation of an organization-owned relationship between two graph nodes.
- **Graph View**: A simple visual presentation that consumes the graph response for one selected asset.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of relationship creation tests confirm analysts and admins can create relationships between two assets in the same organization.
- **SC-002**: 100% of RBAC tests confirm viewers can read relationships and graphs but cannot create relationships.
- **SC-003**: 100% of duplicate relationship tests confirm repeating the same organization, source, target, and relationship type does not increase the relationship count.
- **SC-004**: 100% of cross-tenant tests confirm relationships cannot be created across organizations and graph retrieval never returns another organization's nodes or edges.
- **SC-005**: 100% of missing-asset tests confirm unavailable source, target, or center assets are reported without exposing another organization's data.
- **SC-006**: 100% of relationship listing tests confirm only relationships owned by the authenticated user's organization are returned.
- **SC-007**: 100% of graph retrieval tests confirm the response includes a center object, nodes collection, and edges collection in the documented shape.
- **SC-008**: 100% of graph retrieval tests for connected assets confirm only the selected asset's directly connected relationships appear as edges with directly related assets represented as nodes.
- **SC-009**: 100% of graph retrieval tests for isolated assets confirm the response includes the selected asset in `center` and `nodes` with an empty `edges` collection.
- **SC-010**: 100% of invalid relationship type tests confirm blank, malformed, non-underscore, or unsupported relationship types are rejected with structured errors.
- **SC-011**: 100% of visualization smoke tests confirm it loads graph data from the graph endpoint and renders labeled nodes and edges.
- **SC-012**: A developer or evaluator can use documented Phase 5 instructions to authenticate as seeded users, create assets, create relationships, retrieve a graph, and confirm tenant isolation without public registration or organization creation.

## Assumptions

- Phase 1 has already established the backend application foundation, database connectivity, migration workflow, tests, Docker setup, and README setup notes.
- Phase 2 has already established organizations, users, seeded users, JWT authentication, current-user context, tenant scoping rules, and role-based permissions.
- Phase 3 has already established tenant-scoped asset CRUD, asset validation, structured domain errors, and the asset-not-found response.
- Phase 4 has already established idempotent asset observation behavior, bulk import, lifecycle handling, and organization-scoped asset ingestion.
- Phase 5 is limited to asset relationships, relationship listing, graph retrieval, and simple graph visualization. Rate limiting, caching, CI expansion, and LangChain analysis remain outside this phase.
- Relationship creation is manual through the relationship operation in this phase; automated inference of relationships from imported asset metadata is outside phase 5 unless already available from previous phases.
- The graph endpoint returns a one-hop graph around the selected asset in Phase 5: the center asset, directly connected assets, and directly connected relationships.
- Relationship type values are canonical underscore machine values matching the domain meanings listed in `PLAN.md`.
- The graph visualization is a required demonstration aid for Phase 5, not a separate source of graph business rules.
