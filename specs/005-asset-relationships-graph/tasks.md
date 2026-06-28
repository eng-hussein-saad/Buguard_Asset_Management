# Tasks: Asset Relationships Graph

**Input**: Design documents from `/specs/005-asset-relationships-graph/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/relationships-graph-api.yaml, quickstart.md

**Tests**: Tests are required by the specification and constitution for relationship creation, duplicate prevention, relationship listing, graph retrieval, RBAC, invalid relationship payloads, missing assets, cross-tenant blocking, isolated graph responses, and visualization route behavior. Write tests first and verify they fail before implementation.

**Code Documentation**: Add concise docstrings to all new or modified Python functions, class methods, service methods, repository methods, route handlers, and validators.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete work
- **[Story]**: Maps the task to a user story from spec.md
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Phase 5 starts from the established asset, relationship, RBAC, structured-error, and test foundations.

- [ ] T001 Verify Phase 5 scope, contract, and quickstart alignment in specs/005-asset-relationships-graph/plan.md, specs/005-asset-relationships-graph/spec.md, specs/005-asset-relationships-graph/contracts/relationships-graph-api.yaml, and specs/005-asset-relationships-graph/quickstart.md
- [ ] T002 [P] Audit existing relationship model, enum, unique constraint, RBAC permissions, and repository stub in app/models/asset.py, app/services/rbac.py, app/repositories/relationships.py, and app/services/tenant_assets.py
- [ ] T003 [P] Audit existing asset route, schema, service, repository, and structured error behavior in app/api/routes/assets.py, app/schemas/assets.py, app/services/tenant_assets.py, app/repositories/assets.py, and app/core/errors.py
- [ ] T004 [P] Add reusable relationship test helpers for creating related assets, relationship payloads, and graph assertions in tests/conftest.py
- [ ] T005 [P] Create dedicated Phase 5 relationship integration test module in tests/integration/test_asset_relationships_graph.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schemas, repository helpers, domain errors, service primitives, and route wiring needed before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 [P] Add RelationshipCreate, RelationshipRead, RelationshipList, GraphAsset, GraphEdge, and AssetGraph schemas with extra-field rejection and docstrings in app/schemas/assets.py
- [ ] T007 [P] Add DuplicateRelationshipError with the established structured error envelope and 409 status in app/core/errors.py
- [ ] T008 [P] Add contract tests documenting POST /relationships, GET /relationships, GET /assets/{asset_id}/graph, and GET /assets/{asset_id}/graph/view OpenAPI responses in tests/contract/test_assets_api.py
- [ ] T009 Add duplicate relationship lookup helper scoped by organization_id, source_asset_id, target_asset_id, and relationship_type in app/repositories/relationships.py
- [ ] T010 Add organization-scoped relationship list helper in app/repositories/relationships.py
- [ ] T011 Add one-hop relationship adjacency query helper that loads relationships where the center asset is source or target within one organization in app/repositories/relationships.py
- [ ] T012 Add relationship response and graph response mapping helpers that hide organization_id and produce stable labels in app/services/tenant_assets.py
- [ ] T013 Add relationship route response metadata for 400, 401, 403, 404, and 409 structured errors in app/api/routes/assets.py
- [ ] T014 Add concise docstrings to all new relationship schema, error, repository, service, and route helper code in app/schemas/assets.py, app/core/errors.py, app/repositories/relationships.py, app/services/tenant_assets.py, and app/api/routes/assets.py

**Checkpoint**: Relationship and graph foundations are ready for story implementation.

---

## Phase 3: User Story 1 - Create Tenant-Scoped Relationships (Priority: P1) MVP

**Goal**: Analysts and admins can create one typed relationship between two assets in their organization, duplicate attempts return a structured conflict, and viewers cannot create relationships.

**Independent Test**: Authenticate as an analyst or admin, create two assets in the same organization, create a relationship between them, verify exactly one relationship is stored and visible to organization users, repeat the request for a 409, and verify viewer creation returns 403.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add contract tests for POST /relationships success, 403, 404, 409, and validation response documentation in tests/contract/test_assets_api.py
- [ ] T016 [P] [US1] Add integration tests proving analysts and admins can create relationships between two same-organization assets through POST /relationships in tests/integration/test_asset_relationships_graph.py
- [ ] T017 [P] [US1] Add integration tests proving duplicate relationship creation returns 409 and does not increase the relationship count in tests/integration/test_asset_relationships_graph.py
- [ ] T018 [P] [US1] Add integration tests proving viewers cannot create relationships through POST /relationships in tests/integration/test_asset_rbac.py
- [ ] T019 [P] [US1] Add unit tests for relationship response mapping and duplicate error handling helpers in tests/unit/test_asset_relationships.py

### Implementation for User Story 1

- [ ] T020 [US1] Extend RelationshipCreate validation to accept only source_asset_id, target_asset_id, relationship_type, and metadata while rejecting client organization_id in app/schemas/assets.py
- [ ] T021 [US1] Update create_relationship repository logic to persist metadata and use organization-scoped duplicate protection in app/repositories/relationships.py
- [ ] T022 [US1] Update create_owned_relationship to require CREATE_RELATIONSHIP permission, verify both assets through organization-scoped lookups, reject unavailable assets with AssetNotFoundError, translate duplicate conflicts to DuplicateRelationshipError, commit on success, and rollback on IntegrityError in app/services/tenant_assets.py
- [ ] T023 [US1] Add POST /relationships route with RelationshipCreate input, RelationshipRead output, 201 status, and structured error responses in app/api/routes/assets.py
- [ ] T024 [US1] Ensure relationship creation derives organization_id only from current_user.organization_id and never from request fields in app/services/tenant_assets.py and app/repositories/relationships.py
- [ ] T025 [US1] Add route, service, repository, and schema docstrings for relationship creation and duplicate handling in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/relationships.py, and app/schemas/assets.py

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Block Unsafe or Cross-Tenant Relationships (Priority: P1)

**Goal**: Relationship creation rejects missing assets, cross-organization assets, and client ownership input without revealing other tenants' data.

**Independent Test**: Authenticate as a user in one organization and attempt to create relationships referencing a missing asset, a cross-organization asset, and a payload with organization ownership; verify each fails without exposing another organization's data.

### Tests for User Story 2

- [ ] T026 [P] [US2] Add integration tests for missing source and missing target assets returning the established ASSET_NOT_FOUND response in tests/integration/test_asset_relationships_graph.py
- [ ] T027 [P] [US2] Add integration tests proving cross-organization source or target assets return ASSET_NOT_FOUND and do not create relationships in tests/integration/test_asset_tenant_isolation.py
- [ ] T028 [P] [US2] Add integration tests proving client-supplied organization_id is rejected or ignored before persistence in tests/integration/test_asset_relationships_graph.py
- [ ] T029 [P] [US2] Add integration tests proving malformed, blank, non-underscore, or unsupported relationship_type values fail with structured errors in tests/integration/test_asset_relationships_graph.py

### Implementation for User Story 2

- [ ] T030 [US2] Use organization-scoped asset repository lookups for both source and target availability before relationship creation in app/services/tenant_assets.py
- [ ] T031 [US2] Normalize relationship missing-asset and cross-tenant failures to AssetNotFoundError without leaking whether another organization owns the asset in app/services/tenant_assets.py
- [ ] T032 [US2] Enforce canonical RelationshipType values through Pydantic validation and structured request errors in app/schemas/assets.py
- [ ] T033 [US2] Ensure repository create and duplicate lookup functions always include organization_id predicates in app/repositories/relationships.py
- [ ] T034 [US2] Add docstrings for tenant-safety and validation paths touched by unsafe relationship rejection in app/services/tenant_assets.py, app/repositories/relationships.py, and app/schemas/assets.py

**Checkpoint**: User Stories 1 and 2 both enforce safe relationship creation independently.

---

## Phase 5: User Story 3 - Retrieve an Asset Relationship Graph (Priority: P1)

**Goal**: Viewers, analysts, and admins can retrieve a one-hop graph centered on an organization-owned asset, including the center node, directly connected nodes, and directly connected edges only.

**Independent Test**: Create a small organization-owned graph, authenticate as a viewer in that organization, request GET /assets/{asset_id}/graph, and verify center, nodes, and edges match only organization-owned one-hop relationships.

### Tests for User Story 3

- [ ] T035 [P] [US3] Add contract tests for GET /assets/{asset_id}/graph success and 404 response shapes in tests/contract/test_assets_api.py
- [ ] T036 [P] [US3] Add integration tests proving viewers, analysts, and admins can retrieve graph data for organization-owned assets in tests/integration/test_asset_relationships_graph.py
- [ ] T037 [P] [US3] Add integration tests proving one-hop graph retrieval includes incoming and outgoing edges for the center asset and excludes second-hop relationships in tests/integration/test_asset_relationships_graph.py
- [ ] T038 [P] [US3] Add integration tests proving isolated assets return center in center and nodes with an empty edges collection in tests/integration/test_asset_relationships_graph.py
- [ ] T039 [P] [US3] Add integration tests proving graph retrieval for a cross-organization center asset returns ASSET_NOT_FOUND and never returns foreign nodes or edges in tests/integration/test_asset_tenant_isolation.py
- [ ] T040 [P] [US3] Add unit tests for graph node de-duplication, edge de-duplication, and label mapping helpers in tests/unit/test_asset_relationships.py

### Implementation for User Story 3

- [ ] T041 [US3] Add organization-scoped one-hop graph repository query for relationships where the center asset is source or target in app/repositories/relationships.py
- [ ] T042 [US3] Implement get_asset_graph service with READ_GRAPH permission, organization-scoped center asset lookup, one-hop adjacency loading, node de-duplication, edge de-duplication, and AssetGraph schema mapping in app/services/tenant_assets.py
- [ ] T043 [US3] Add GET /assets/{asset_id}/graph route with AssetGraph output and structured 401 and 404 responses in app/api/routes/assets.py
- [ ] T044 [US3] Ensure graph response schemas expose center, nodes, and edges without organization_id and with labels derived from asset values and relationship types in app/schemas/assets.py
- [ ] T045 [US3] Add docstrings for graph retrieval route, service, repository query, and mapping helpers in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/relationships.py, and app/schemas/assets.py

**Checkpoint**: All P1 stories are independently functional and tenant scoped.

---

## Phase 6: User Story 4 - List Organization Relationships (Priority: P2)

**Goal**: Viewers, analysts, and admins can list only relationships owned by their organization, including empty-list behavior.

**Independent Test**: Authenticate as each role, list relationships after creating several organization-owned relationships, and verify only relationships from the authenticated user's organization are returned.

### Tests for User Story 4

- [ ] T046 [P] [US4] Add contract tests for GET /relationships response shape and authentication responses in tests/contract/test_assets_api.py
- [ ] T047 [P] [US4] Add integration tests proving viewer, analyst, and admin users can list organization-owned relationships in tests/integration/test_asset_relationships_graph.py
- [ ] T048 [P] [US4] Add integration tests proving relationship listing returns an empty items collection when the organization has no relationships in tests/integration/test_asset_relationships_graph.py
- [ ] T049 [P] [US4] Add integration tests proving relationship listing excludes relationships owned by other organizations in tests/integration/test_asset_tenant_isolation.py

### Implementation for User Story 4

- [ ] T050 [US4] Implement list_relationships service with READ_RELATIONSHIPS permission and organization-scoped repository access in app/services/tenant_assets.py
- [ ] T051 [US4] Implement GET /relationships route with RelationshipList output and structured authentication response documentation in app/api/routes/assets.py
- [ ] T052 [US4] Ensure relationship list responses hide organization_id and serialize metadata and created_at consistently in app/schemas/assets.py and app/services/tenant_assets.py
- [ ] T053 [US4] Add docstrings for relationship listing route, service, repository, and schema paths in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/relationships.py, and app/schemas/assets.py

**Checkpoint**: Relationship reads are observable and tenant scoped for all reader roles.

---

## Phase 7: User Story 5 - View a Simple Graph Visualization (Priority: P3)

**Goal**: Evaluators and developers can open a simple graph view that fetches the graph endpoint, renders labeled nodes and edges, and displays structured error states.

**Independent Test**: Authenticate as a user with graph access, open the visualization for an organization-owned asset, and verify it fetches GET /assets/{asset_id}/graph and renders returned labels without duplicating backend traversal rules.

### Tests for User Story 5

- [ ] T054 [P] [US5] Add contract tests for GET /assets/{asset_id}/graph/view text/html response documentation in tests/contract/test_assets_api.py
- [ ] T055 [P] [US5] Add integration tests proving the graph view route returns an HTML shell that references GET /assets/{asset_id}/graph for the supplied asset id in tests/integration/test_asset_relationships_graph.py
- [ ] T056 [P] [US5] Add integration tests proving the graph view route requires authentication and preserves structured authentication errors in tests/integration/test_asset_relationships_graph.py

### Implementation for User Story 5

- [ ] T057 [US5] Implement a minimal authenticated graph visualization HTML route for GET /assets/{asset_id}/graph/view in app/api/routes/assets.py
- [ ] T058 [US5] Ensure the visualization JavaScript fetches /assets/{asset_id}/graph, renders node labels from asset values, renders edge labels from relationship types, and displays structured error payloads without independent graph traversal in app/api/routes/assets.py
- [ ] T059 [US5] Keep visualization route behavior documented as a simple evaluator aid without adding new runtime settings in README.md and .env.example
- [ ] T060 [US5] Add docstrings for the graph visualization route and any helper functions in app/api/routes/assets.py

**Checkpoint**: All user stories are independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, and cleanup across Phase 5.

- [ ] T061 [P] Update README.md with Phase 5 authentication, relationship creation, duplicate prevention, relationship listing, graph retrieval, visualization usage, and tenant-isolation evaluator steps in README.md
- [ ] T062 [P] Confirm no new Phase 5 runtime settings are required or document any new required setting in .env.example
- [ ] T063 [P] Add or update concise docstrings for all modified Python functions, class methods, services, repositories, routes, validators, and helpers in app/
- [ ] T064 [P] Review relationship list and graph retrieval for bounded organization-scoped queries, one-hop-only behavior, duplicate node removal, and duplicate edge removal in app/repositories/relationships.py and app/services/tenant_assets.py
- [ ] T065 [P] Review structured error codes and messages for ASSET_NOT_FOUND, DUPLICATE_RELATIONSHIP, authorization failures, authentication failures, and invalid relationship payloads in app/core/errors.py, app/schemas/assets.py, and app/api/routes/assets.py
- [ ] T066 Run quickstart validation steps from specs/005-asset-relationships-graph/quickstart.md
- [ ] T067 Run `uv run pytest tests/unit/test_asset_relationships.py`
- [ ] T068 Run `uv run pytest tests/contract/test_assets_api.py`
- [ ] T069 Run `uv run pytest tests/integration/test_asset_relationships_graph.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py`
- [ ] T070 Run `uv run pytest tests/contract tests/integration tests/unit`
- [ ] T071 Run `uv run pytest` against the full tests/ suite
- [ ] T072 Run `uv run ruff check .` using configuration in pyproject.toml
- [ ] T073 Run `uv run mypy app` against the app/ package

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP delivery for relationship creation.
- **User Story 2 (Phase 4)**: Depends on Foundational and hardens US1 creation paths against unsafe inputs.
- **User Story 3 (Phase 5)**: Depends on Foundational and can use US1-created relationship data for validation.
- **User Story 4 (Phase 6)**: Depends on Foundational and is most useful after US1 relationship creation exists.
- **User Story 5 (Phase 7)**: Depends on US3 graph retrieval because the view must consume the graph endpoint.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Create Tenant-Scoped Relationships**: MVP, no story dependency after Foundation.
- **US2 Block Unsafe or Cross-Tenant Relationships**: Can start after Foundation, but final validation depends on US1 relationship creation behavior.
- **US3 Retrieve an Asset Relationship Graph**: Can start after Foundation, but connected graph validation depends on relationship creation from US1.
- **US4 List Organization Relationships**: Can start after Foundation, with meaningful non-empty validation depending on US1.
- **US5 View a Simple Graph Visualization**: Depends on US3 graph retrieval and should not duplicate graph business rules.

### Within Each User Story

- Write tests first and verify they fail before implementation.
- Schemas and contract documentation before route implementation.
- Repository helpers before service orchestration.
- Service validation, RBAC, tenant scoping, and error mapping before route wiring.
- Story complete before moving to lower-priority work unless tasks are explicitly parallel.

## Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001.
- T006, T007, and T008 can run in parallel because schemas, errors, and contract tests touch different files.
- T009, T010, and T011 can run in parallel once repository naming is agreed.
- T012 and T013 can run in parallel after schema names are known.
- US1 tests T015-T019 can run in parallel before implementation.
- US2 tests T026-T029 can run in parallel before implementation.
- US3 tests T035-T040 can run in parallel before implementation.
- US4 tests T046-T049 can run in parallel before implementation.
- US5 tests T054-T056 can run in parallel before implementation.
- Documentation, environment, docstring, performance, and error reviews T061-T065 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T015 [P] [US1] Add contract tests for POST /relationships success, 403, 404, 409, and validation response documentation in tests/contract/test_assets_api.py"
Task: "T016 [P] [US1] Add integration tests proving analysts and admins can create relationships between two same-organization assets through POST /relationships in tests/integration/test_asset_relationships_graph.py"
Task: "T017 [P] [US1] Add integration tests proving duplicate relationship creation returns 409 and does not increase the relationship count in tests/integration/test_asset_relationships_graph.py"
Task: "T018 [P] [US1] Add integration tests proving viewers cannot create relationships through POST /relationships in tests/integration/test_asset_rbac.py"
```

## Parallel Example: User Story 2

```bash
Task: "T026 [P] [US2] Add integration tests for missing source and missing target assets returning the established ASSET_NOT_FOUND response in tests/integration/test_asset_relationships_graph.py"
Task: "T027 [P] [US2] Add integration tests proving cross-organization source or target assets return ASSET_NOT_FOUND and do not create relationships in tests/integration/test_asset_tenant_isolation.py"
Task: "T028 [P] [US2] Add integration tests proving client-supplied organization_id is rejected or ignored before persistence in tests/integration/test_asset_relationships_graph.py"
Task: "T029 [P] [US2] Add integration tests proving malformed, blank, non-underscore, or unsupported relationship_type values fail with structured errors in tests/integration/test_asset_relationships_graph.py"
```

## Parallel Example: User Story 3

```bash
Task: "T035 [P] [US3] Add contract tests for GET /assets/{asset_id}/graph success and 404 response shapes in tests/contract/test_assets_api.py"
Task: "T036 [P] [US3] Add integration tests proving viewers, analysts, and admins can retrieve graph data for organization-owned assets in tests/integration/test_asset_relationships_graph.py"
Task: "T037 [P] [US3] Add integration tests proving one-hop graph retrieval includes incoming and outgoing edges for the center asset and excludes second-hop relationships in tests/integration/test_asset_relationships_graph.py"
Task: "T040 [P] [US3] Add unit tests for graph node de-duplication, edge de-duplication, and label mapping helpers in tests/unit/test_asset_relationships.py"
```

## Parallel Example: User Story 4

```bash
Task: "T046 [P] [US4] Add contract tests for GET /relationships response shape and authentication responses in tests/contract/test_assets_api.py"
Task: "T047 [P] [US4] Add integration tests proving viewer, analyst, and admin users can list organization-owned relationships in tests/integration/test_asset_relationships_graph.py"
Task: "T048 [P] [US4] Add integration tests proving relationship listing returns an empty items collection when the organization has no relationships in tests/integration/test_asset_relationships_graph.py"
Task: "T049 [P] [US4] Add integration tests proving relationship listing excludes relationships owned by other organizations in tests/integration/test_asset_tenant_isolation.py"
```

## Parallel Example: User Story 5

```bash
Task: "T054 [P] [US5] Add contract tests for GET /assets/{asset_id}/graph/view text/html response documentation in tests/contract/test_assets_api.py"
Task: "T055 [P] [US5] Add integration tests proving the graph view route returns an HTML shell that references GET /assets/{asset_id}/graph for the supplied asset id in tests/integration/test_asset_relationships_graph.py"
Task: "T056 [P] [US5] Add integration tests proving the graph view route requires authentication and preserves structured authentication errors in tests/integration/test_asset_relationships_graph.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup checks and shared relationship test scaffolding.
2. Complete Phase 2 shared relationship schemas, errors, repository helpers, service helpers, and contract documentation.
3. Complete Phase 3 User Story 1 to deliver safe POST /relationships for same-organization assets.
4. Stop and validate User Story 1 independently with T015-T025.
5. Complete Phase 4 unsafe and cross-tenant relationship blocking.
6. Complete Phase 5 graph retrieval as the main read outcome.
7. Add Phase 6 relationship listing.
8. Add Phase 7 simple graph visualization after the graph endpoint is stable.

### Incremental Delivery

- Deliver all P1 stories first: US1, US2, and US3.
- Treat US4 as the P2 observability layer after creation and graph retrieval are stable.
- Treat US5 as the P3 evaluator aid and keep it endpoint-driven.
- Run story-specific tests before broader validation commands.
- Use quickstart.md as the final evaluator-facing verification path.

### Notes

- [P] tasks use separate files or can be executed independently.
- [US1], [US2], [US3], [US4], and [US5] labels map directly to spec.md user stories.
- Every route, service, repository, and schema task must preserve tenant scoping and avoid client-supplied organization ownership.
- Graph retrieval remains one-hop only for Phase 5; recursive traversal, caching, rate limiting, CI expansion, automated inference, and AI analysis remain out of scope.
