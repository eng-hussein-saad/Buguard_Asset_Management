# Tasks: Asset CRUD

**Input**: Design documents from `/specs/003-asset-crud/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/assets-api.yaml, quickstart.md

**Tests**: Tests are required by the specification and constitution for CRUD behavior, tenant isolation, RBAC, validation, structured errors, filtering, sorting, pagination, duplicate handling, and normalization. Write tests first and verify they fail before implementation.

**Code Documentation**: Add concise docstrings to all new or modified Python functions, class methods, service methods, and repository methods.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete work
- **[Story]**: Maps the task to a user story from spec.md
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Phase 3 starts from the established backend foundation and add the missing asset API module skeleton.

- [ ] T001 Verify existing FastAPI, SQLAlchemy, Alembic, auth, RBAC, and seed-user foundations against specs/003-asset-crud/plan.md
- [ ] T002 [P] Create asset schema module skeleton in app/schemas/assets.py
- [ ] T003 [P] Create asset route module skeleton in app/api/routes/assets.py
- [ ] T004 Register the asset route module in app/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared asset validation, persistence, error, and permission foundations that must exist before story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 [P] Add asset type, status, sort, pagination, create, update, response, and error schema definitions in app/schemas/assets.py
- [ ] T006 [P] Add `ASSET_NOT_FOUND` and `DUPLICATE_ASSET` AppError helpers in app/core/errors.py
- [ ] T007 Add asset value normalization helpers for trim and domain/subdomain lowercase behavior in app/services/tenant_assets.py
- [ ] T008 Add repository helpers for organization-scoped asset lookup and duplicate lookup in app/repositories/assets.py
- [ ] T009 Add service permission helpers using existing RBAC permissions in app/services/tenant_assets.py
- [ ] T010 Confirm Asset model fields, metadata alias handling, timestamps, tags, and uniqueness constraint support Phase 3 in app/models/asset.py
- [ ] T011 [P] Add shared asset test fixtures and multi-tenant asset factories in tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order or in parallel where dependencies allow.

---

## Phase 3: User Story 1 - Manage Organization Assets (Priority: P1) MVP

**Goal**: Analysts and admins can create, inspect, update, and hard delete organization-owned assets while viewers are blocked from mutations.

**Independent Test**: Authenticate seeded analyst, admin, and viewer users; create an asset without client ownership, read it back, update editable fields, verify admin-only hard delete, and verify viewer mutation attempts return structured forbidden errors.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add contract tests for POST /assets, GET /assets/{asset_id}, PATCH /assets/{asset_id}, and DELETE /assets/{asset_id} success and documented response shapes in tests/contract/test_assets_api.py
- [ ] T013 [P] [US1] Add integration tests for analyst create/update/read and admin hard delete in tests/integration/test_asset_crud.py
- [ ] T014 [P] [US1] Add integration tests for viewer mutation denial and analyst delete denial in tests/integration/test_asset_rbac.py
- [ ] T015 [P] [US1] Add unit tests for trim and domain/subdomain lowercase normalization before create/update in tests/unit/test_asset_normalization.py

### Implementation for User Story 1

- [ ] T016 [US1] Implement AssetCreate, AssetUpdate, AssetRead, and domain enum schemas with extra-field rejection in app/schemas/assets.py
- [ ] T017 [US1] Implement create, detail, update, and hard-delete repository methods scoped by organization_id in app/repositories/assets.py
- [ ] T018 [US1] Implement create, get, update, and delete service methods with normalization, RBAC checks, duplicate checks, and structured error mapping in app/services/tenant_assets.py
- [ ] T019 [US1] Implement POST /assets, GET /assets/{asset_id}, PATCH /assets/{asset_id}, and DELETE /assets/{asset_id} route handlers with response models and summaries in app/api/routes/assets.py
- [ ] T020 [US1] Ensure create and update payloads reject organization_id and other extra fields in app/schemas/assets.py
- [ ] T021 [US1] Map database uniqueness races to structured HTTP 409 duplicate responses in app/services/tenant_assets.py
- [ ] T022 [US1] Add concise docstrings to new and modified asset CRUD functions in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/assets.py, and app/schemas/assets.py

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Find and Browse Assets (Priority: P1)

**Goal**: Viewers, analysts, and admins can list and read organization-owned assets with supported filters, sorting, and bounded pagination.

**Independent Test**: Seed assets for two organizations, authenticate each role, and verify list/detail/filter/sort/pagination only returns assets owned by the authenticated user's organization.

### Tests for User Story 2

- [ ] T023 [P] [US2] Add contract tests for GET /assets query parameters and paginated response metadata in tests/contract/test_assets_api.py
- [ ] T024 [P] [US2] Add integration tests for type, status, tag, source, and value_contains filters in tests/integration/test_asset_filters.py
- [ ] T025 [P] [US2] Add integration tests for all supported sort fields and asc/desc order in tests/integration/test_asset_filters.py
- [ ] T026 [P] [US2] Add integration tests for default pagination, max page_size 100, empty results, and page metadata in tests/integration/test_asset_filters.py

### Implementation for User Story 2

- [ ] T027 [US2] Implement AssetListParams and PaginatedAssets schemas with filter, sort, and pagination validation in app/schemas/assets.py
- [ ] T028 [US2] Implement organization-scoped filtered count and paginated list queries in app/repositories/assets.py
- [ ] T029 [US2] Implement list service method with normalized value_contains handling and page metadata calculation in app/services/tenant_assets.py
- [ ] T030 [US2] Implement GET /assets route handler with query validation, response model, and OpenAPI summary in app/api/routes/assets.py
- [ ] T031 [US2] Ensure tag containment, source matching, and value_contains filters never remove organization scoping in app/repositories/assets.py
- [ ] T032 [US2] Add concise docstrings to new and modified list/filter/sort/pagination functions in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/assets.py, and app/schemas/assets.py

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Preserve Tenant Isolation (Priority: P1)

**Goal**: Asset operations are strictly limited to the authenticated user's organization and do not leak cross-tenant existence.

**Independent Test**: Create matching and distinct assets in two organizations, authenticate users from each organization, and verify every asset CRUD and list operation is scoped to the authenticated user's organization.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add integration tests for same type/value assets existing independently in two organizations in tests/integration/test_asset_tenant_isolation.py
- [ ] T034 [P] [US3] Add integration tests that cross-organization detail, update, and delete return ASSET_NOT_FOUND in tests/integration/test_asset_tenant_isolation.py
- [ ] T035 [P] [US3] Add integration tests that client-supplied organization_id in create and update is rejected in tests/integration/test_asset_tenant_isolation.py
- [ ] T036 [P] [US3] Add list isolation tests for filters and value_contains across organizations in tests/integration/test_asset_tenant_isolation.py

### Implementation for User Story 3

- [ ] T037 [US3] Audit every asset repository query to require organization_id predicates in app/repositories/assets.py
- [ ] T038 [US3] Audit every asset service method to derive organization_id only from the authenticated user context in app/services/tenant_assets.py
- [ ] T039 [US3] Ensure cross-organization detail, update, and delete paths raise the same ASSET_NOT_FOUND error as missing assets in app/services/tenant_assets.py
- [ ] T040 [US3] Ensure route signatures do not accept organization ownership from path, query, or body parameters in app/api/routes/assets.py and app/schemas/assets.py

**Checkpoint**: All P1 user stories are independently functional and tenant scoped.

---

## Phase 6: User Story 4 - Receive Clear Validation and Error Responses (Priority: P2)

**Goal**: Invalid requests, not-found cases, forbidden actions, duplicate creates, and API documentation return consistent, understandable results.

**Independent Test**: Submit invalid payloads, unsupported filters and sort options, missing assets, forbidden actions, unauthenticated requests, and duplicate creates, then verify response envelopes and OpenAPI documentation.

### Tests for User Story 4

- [ ] T041 [P] [US4] Add validation tests for unsupported asset type, unsupported status, blank values, empty update bodies, and extra fields in tests/contract/test_assets_api.py
- [ ] T042 [P] [US4] Add validation tests for unsupported sort fields, unsupported sort orders, page < 1, page_size < 1, and page_size > 100 in tests/integration/test_asset_filters.py
- [ ] T043 [P] [US4] Add structured error tests for ASSET_NOT_FOUND, authorization_failed, DUPLICATE_ASSET, and unauthenticated access in tests/integration/test_asset_crud.py and tests/integration/test_asset_rbac.py
- [ ] T044 [P] [US4] Add OpenAPI schema tests for Assets tags, route summaries, request models, response models, and documented errors in tests/contract/test_assets_api.py

### Implementation for User Story 4

- [ ] T045 [US4] Harden Pydantic validators for asset payloads, filters, sorting, and pagination in app/schemas/assets.py
- [ ] T046 [US4] Add structured response documentation and error examples to all asset route decorators in app/api/routes/assets.py
- [ ] T047 [US4] Ensure AppError handling returns `{ "error": { "code": "...", "message": "...", "details": {} } }` for asset domain failures in app/core/errors.py
- [ ] T048 [US4] Ensure duplicate creates and duplicate updates return HTTP 409 with DUPLICATE_ASSET in app/services/tenant_assets.py
- [ ] T049 [US4] Ensure forbidden asset actions use the stable authorization_failed code through app/services/rbac.py and app/services/tenant_assets.py

**Checkpoint**: All user stories are independently functional with documented validation and error behavior.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, and cleanup across Phase 3.

- [ ] T050 [P] Update README.md with Phase 3 asset authentication, create, list, filter, update, delete, and test commands
- [ ] T051 [P] Confirm `.env.example` needs no new Phase 3 settings or document any new required runtime key in .env.example
- [ ] T052 [P] Add or update concise docstrings for all modified Python functions, class methods, services, and repositories in app/
- [ ] T053 Run quickstart validation steps from specs/003-asset-crud/quickstart.md
- [ ] T054 Run `uv run pytest tests/unit/test_asset_normalization.py`
- [ ] T055 Run `uv run pytest tests/contract/test_assets_api.py`
- [ ] T056 Run `uv run pytest tests/integration/test_asset_crud.py tests/integration/test_asset_filters.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py`
- [ ] T057 Run `uv run pytest`
- [ ] T058 Run `uv run ruff check .`
- [ ] T059 Run `uv run mypy app`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP delivery.
- **User Story 2 (Phase 4)**: Depends on Foundational and can share US1 detail schemas, but list behavior is independently testable.
- **User Story 3 (Phase 5)**: Depends on Foundational and should be validated against US1 and US2 operations.
- **User Story 4 (Phase 6)**: Depends on the implemented routes and services from US1, US2, and US3.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Manage Organization Assets**: MVP, no story dependency after Foundation.
- **US2 Find and Browse Assets**: Can start after Foundation; uses shared response schemas and repository scoping.
- **US3 Preserve Tenant Isolation**: Can start after Foundation; validates all asset operations and should be repeated after US1 and US2.
- **US4 Receive Clear Validation and Error Responses**: Best after US1-US3 because it hardens their error/documentation surface.

### Within Each User Story

- Write tests first and verify they fail before implementation.
- Schemas and route contracts before route implementation.
- Repository methods before service orchestration.
- Service normalization, RBAC, and error mapping before route wiring.
- Story complete before moving to lower-priority work unless tasks are explicitly parallel.

## Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T005, T006, and T011 can run in parallel because they touch separate schema, error, and test fixture files.
- US1 tests T012-T015 can run in parallel before implementation.
- US2 tests T023-T026 can run in parallel before implementation.
- US3 tests T033-T036 can run in parallel before implementation.
- US4 tests T041-T044 can run in parallel before implementation.
- Documentation and environment checks T050-T052 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T012 [P] [US1] Add contract tests for POST /assets, GET /assets/{asset_id}, PATCH /assets/{asset_id}, and DELETE /assets/{asset_id} success and documented response shapes in tests/contract/test_assets_api.py"
Task: "T013 [P] [US1] Add integration tests for analyst create/update/read and admin hard delete in tests/integration/test_asset_crud.py"
Task: "T014 [P] [US1] Add integration tests for viewer mutation denial and analyst delete denial in tests/integration/test_asset_rbac.py"
Task: "T015 [P] [US1] Add unit tests for trim and domain/subdomain lowercase normalization before create/update in tests/unit/test_asset_normalization.py"
```

## Parallel Example: User Story 2

```bash
Task: "T023 [P] [US2] Add contract tests for GET /assets query parameters and paginated response metadata in tests/contract/test_assets_api.py"
Task: "T024 [P] [US2] Add integration tests for type, status, tag, source, and value_contains filters in tests/integration/test_asset_filters.py"
Task: "T025 [P] [US2] Add integration tests for all supported sort fields and asc/desc order in tests/integration/test_asset_filters.py"
Task: "T026 [P] [US2] Add integration tests for default pagination, max page_size 100, empty results, and page metadata in tests/integration/test_asset_filters.py"
```

## Parallel Example: User Story 3

```bash
Task: "T033 [P] [US3] Add integration tests for same type/value assets existing independently in two organizations in tests/integration/test_asset_tenant_isolation.py"
Task: "T034 [P] [US3] Add integration tests that cross-organization detail, update, and delete return ASSET_NOT_FOUND in tests/integration/test_asset_tenant_isolation.py"
Task: "T035 [P] [US3] Add integration tests that client-supplied organization_id in create and update is rejected in tests/integration/test_asset_tenant_isolation.py"
Task: "T036 [P] [US3] Add list isolation tests for filters and value_contains across organizations in tests/integration/test_asset_tenant_isolation.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup checks and asset route/schema skeletons.
2. Complete Phase 2 shared schema, error, repository, service, and fixture foundations.
3. Complete Phase 3 User Story 1 to deliver create, detail, update, delete, RBAC, duplicates, and normalization.
4. Stop and validate User Story 1 independently with T012-T022.
5. Add User Story 2 list/filter/sort/pagination behavior.
6. Re-run and harden tenant-isolation coverage through User Story 3.
7. Finish User Story 4 validation, structured errors, and OpenAPI polish.

### Incremental Delivery

- Deliver P1 stories first: US1, US2, and US3.
- Keep US4 error and documentation polish visible but secondary to functional P1 behavior.
- Run story-specific tests before broader validation commands.
- Use quickstart.md as the final evaluator-facing verification path.

### Notes

- [P] tasks use separate files or can be executed independently.
- [US1], [US2], [US3], and [US4] labels map directly to spec.md user stories.
- Every route, service, repository, and schema task must preserve tenant scoping and avoid client-supplied organization ownership.
- Hard delete is Phase 3 behavior; import lifecycle, relationship APIs, graph retrieval, rate limiting, caching, and AI analysis remain out of scope.
