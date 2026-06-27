# Tasks: Bulk Import Lifecycle

**Input**: Design documents from `/specs/004-bulk-import-lifecycle/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/bulk-import-api.yaml, quickstart.md

**Tests**: Tests are required by the specification and constitution for idempotent import, duplicate records within one batch, tag and metadata merge behavior, malformed records, partial-failure and all-record-failure statuses, stale reactivation, archived asset import behavior, stale update permissions, server-time timestamps, and tenant isolation. Write tests first and verify they fail before implementation.

**Code Documentation**: Add concise docstrings to all new or modified Python functions, class methods, service methods, repository methods, and validators.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete work
- **[Story]**: Maps the task to a user story from spec.md
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Phase 4 starts from the established asset CRUD foundation and add shared import test scaffolding.

- [ ] T001 Verify Phase 4 scope, contract, and quickstart alignment in specs/004-bulk-import-lifecycle/plan.md, specs/004-bulk-import-lifecycle/spec.md, specs/004-bulk-import-lifecycle/contracts/bulk-import-api.yaml, and specs/004-bulk-import-lifecycle/quickstart.md
- [ ] T002 [P] Audit existing asset schema, route, service, repository, model, and error foundations in app/schemas/assets.py, app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/assets.py, app/models/asset.py, and app/core/errors.py
- [ ] T003 [P] Add reusable bulk import request payload and assertion helpers for Phase 4 tests in tests/conftest.py
- [ ] T004 [P] Create dedicated Phase 4 import integration test module in tests/integration/test_asset_import_lifecycle.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared import schemas, validation helpers, repository helpers, service primitives, and route documentation needed before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 [P] Add AssetImportBatch, AssetImportRecord, AssetImportSummary, and AssetImportError schemas with extra-field rejection, explicit ignored lifecycle timestamp aliases, and docstrings in app/schemas/assets.py
- [ ] T006 [P] Add contract tests for POST /assets/import OpenAPI request, response, and error documentation in tests/contract/test_assets_api.py
- [ ] T007 Add organization-scoped lookup helper by organization_id, type, and canonical value for import deduplication in app/repositories/assets.py
- [ ] T008 Add repository helper for import-safe asset updates of status, last_seen, source, tags, and metadata in app/repositories/assets.py
- [ ] T009 Add import merge helpers for ordered tag de-duplication and shallow newest-wins metadata merge in app/services/tenant_assets.py
- [ ] T010 Add import lifecycle helper for new, active, stale, and archived status transitions in app/services/tenant_assets.py
- [ ] T011 Add per-record import validation helper that returns stable index and reason failures, rejects organization_id and unknown timestamp fields, ignores only client first_seen and last_seen fields, and never trusts client ownership or timestamps in app/services/tenant_assets.py
- [ ] T012 Add import summary status mapping helper for HTTP 200, 207, and 422 outcomes in app/services/tenant_assets.py
- [ ] T013 Add concise docstrings to all new import schema, repository, and service helpers in app/schemas/assets.py, app/repositories/assets.py, and app/services/tenant_assets.py

**Checkpoint**: Import foundations are ready for story implementation.

---

## Phase 3: User Story 1 - Import Assets Idempotently (Priority: P1) MVP

**Goal**: Analysts and admins can import valid asset observations without duplicate assets, including repeated datasets and duplicate records in one batch.

**Independent Test**: Authenticate as an analyst or admin, import a valid dataset, import the same dataset again, and verify the organization asset count does not increase while existing assets are reported as updated.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract tests for POST /assets/import success response shape, created counts, updated counts, and stable summary fields in tests/contract/test_assets_api.py
- [ ] T015 [P] [US1] Add integration tests for first import creating organization-owned assets through POST /assets/import in tests/integration/test_asset_import_lifecycle.py
- [ ] T016 [P] [US1] Add integration tests proving re-importing the same dataset does not increase organization asset count in tests/integration/test_asset_import_lifecycle.py
- [ ] T017 [P] [US1] Add integration tests proving duplicate records in one batch become one create plus updates in tests/integration/test_asset_import_lifecycle.py
- [ ] T018 [P] [US1] Add integration tests proving same type and value imports remain independent across two organizations in tests/integration/test_asset_tenant_isolation.py

### Implementation for User Story 1

- [ ] T019 [US1] Implement import service orchestration with analyst/admin RBAC, canonical value matching, idempotent create/update behavior, and commit/rollback handling in app/services/tenant_assets.py
- [ ] T020 [US1] Implement POST /assets/import route with AssetImportBatch input, AssetImportSummary output, response status selection, and documented 200/207/422 responses in app/api/routes/assets.py
- [ ] T021 [US1] Ensure import creates derive organization_id only from current_user.organization_id and never from request fields in app/services/tenant_assets.py and app/repositories/assets.py
- [ ] T022 [US1] Ensure repeated dataset imports use the existing organization/type/value unique constraint as the duplicate guard in app/repositories/assets.py
- [ ] T023 [US1] Add route, service, and repository docstrings for idempotent import behavior in app/api/routes/assets.py, app/services/tenant_assets.py, and app/repositories/assets.py

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Refresh Existing Asset Observations (Priority: P1)

**Goal**: Re-imported assets refresh observation state while preserving original discovery history and predictable lifecycle rules.

**Independent Test**: Create or import an asset, re-import it later with new tags and metadata, then verify first_seen is preserved, last_seen changes to server processing time, tags and metadata merge predictably, stale assets become active, and archived assets only reactivate on explicit active status.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add integration tests for first_seen preservation and server-owned last_seen refresh on re-import in tests/integration/test_asset_import_lifecycle.py
- [ ] T025 [P] [US2] Add integration tests for ordered tag merge without duplicate tag values in tests/integration/test_asset_import_lifecycle.py
- [ ] T026 [P] [US2] Add integration tests for shallow metadata merge preserving non-conflicting keys and replacing conflicting keys in tests/integration/test_asset_import_lifecycle.py
- [ ] T027 [P] [US2] Add integration tests proving stale assets become active when re-imported in tests/integration/test_asset_import_lifecycle.py
- [ ] T028 [P] [US2] Add integration tests proving archived assets remain archived unless import record explicitly sets status active in tests/integration/test_asset_import_lifecycle.py
- [ ] T029 [P] [US2] Add unit tests for tag merge, metadata merge, and lifecycle transition helpers in tests/unit/test_asset_normalization.py

### Implementation for User Story 2

- [ ] T030 [US2] Apply server processing time to created and accepted re-imported records while ignoring only client first_seen and last_seen fields and rejecting unknown timestamp fields in app/services/tenant_assets.py
- [ ] T031 [US2] Preserve first_seen and update last_seen during existing asset import updates in app/services/tenant_assets.py and app/repositories/assets.py
- [ ] T032 [US2] Apply ordered tag de-duplication and shallow metadata merge for import updates in app/services/tenant_assets.py
- [ ] T033 [US2] Implement stale-to-active reactivation on accepted re-sighting in app/services/tenant_assets.py
- [ ] T034 [US2] Implement archived import behavior that keeps archived status unless the import record explicitly sets status active in app/services/tenant_assets.py
- [ ] T035 [US2] Add docstrings for lifecycle timestamp, tag merge, metadata merge, stale reactivation, and archived reactivation helpers in app/services/tenant_assets.py

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Report Partial Import Failures (Priority: P1)

**Goal**: Malformed import records are reported by input index and reason without preventing valid records in the same well-formed batch from being saved.

**Independent Test**: Submit a batch with valid and malformed records and verify valid records are saved, failed records are reported with zero-based indexes and readable reasons, and HTTP 207 is returned. Submit a batch where every record fails and verify no assets change and HTTP 422 uses the same summary shape.

### Tests for User Story 3

- [ ] T036 [P] [US3] Add contract tests for HTTP 207 and HTTP 422 AssetImportSummary response shape in tests/contract/test_assets_api.py
- [ ] T037 [P] [US3] Add integration tests for mixed valid, missing value, blank value, unsupported type, and unsupported status records returning HTTP 207 in tests/integration/test_asset_import_lifecycle.py
- [ ] T038 [P] [US3] Add integration tests for all-record failure returning HTTP 422 without creating or updating assets in tests/integration/test_asset_import_lifecycle.py
- [ ] T039 [P] [US3] Add integration tests for malformed tags, metadata, unknown extra fields including observed_at, and client organization_id being rejected per record, while client first_seen and last_seen fields are ignored, in tests/integration/test_asset_import_lifecycle.py
- [ ] T040 [P] [US3] Add integration tests proving per-record import errors do not reveal cross-tenant asset data in tests/integration/test_asset_tenant_isolation.py

### Implementation for User Story 3

- [ ] T041 [US3] Convert per-record validation failures into stable AssetImportError entries with original zero-based indexes in app/services/tenant_assets.py
- [ ] T042 [US3] Continue processing valid records after malformed records in the same well-formed batch in app/services/tenant_assets.py
- [ ] T043 [US3] Return HTTP 207 when at least one record succeeds and at least one record fails in app/api/routes/assets.py and app/services/tenant_assets.py
- [ ] T044 [US3] Return HTTP 422 with the same AssetImportSummary shape when every record fails in app/api/routes/assets.py and app/services/tenant_assets.py
- [ ] T045 [US3] Preserve structured domain error envelopes for authentication, authorization, malformed JSON, and invalid batch-shape failures outside per-record import errors in app/core/errors.py and app/api/routes/assets.py
- [ ] T046 [US3] Add docstrings for per-record validation, partial-failure summary, and status-mapping helpers in app/services/tenant_assets.py and app/api/routes/assets.py

**Checkpoint**: All P1 user stories are independently functional and tenant scoped.

---

## Phase 6: User Story 4 - Mark Assets Stale Through Asset Update (Priority: P2)

**Goal**: Analysts and admins can mark organization-owned assets stale through PATCH /assets/{asset_id}, viewers are denied, cross-organization references behave like missing assets, and imports can reactivate stale assets.

**Independent Test**: Authenticate as an analyst or admin, PATCH an owned active asset with status stale, verify viewers cannot perform the update, verify cross-organization updates return ASSET_NOT_FOUND, and verify re-importing the stale asset makes it active.

### Tests for User Story 4

- [ ] T047 [P] [US4] Add contract tests documenting PATCH /assets/{asset_id} with status stale and 403/404 responses in tests/contract/test_assets_api.py
- [ ] T048 [P] [US4] Add integration tests for analyst and admin stale status updates through PATCH /assets/{asset_id} in tests/integration/test_asset_crud.py
- [ ] T049 [P] [US4] Add integration tests for viewer stale update denial and analyst/admin permission boundaries in tests/integration/test_asset_rbac.py
- [ ] T050 [P] [US4] Add integration tests for cross-organization stale update returning ASSET_NOT_FOUND in tests/integration/test_asset_tenant_isolation.py
- [ ] T051 [P] [US4] Add integration test proving re-importing a stale asset after PATCH /assets/{asset_id} reactivates it in tests/integration/test_asset_import_lifecycle.py

### Implementation for User Story 4

- [ ] T052 [US4] Verify AssetUpdate accepts status stale while still rejecting empty bodies, invalid statuses, and ownership fields in app/schemas/assets.py
- [ ] T053 [US4] Ensure PATCH /assets/{asset_id} stale updates use existing UPDATE_ASSET permission checks and organization-scoped lookup in app/services/tenant_assets.py
- [ ] T054 [US4] Ensure cross-organization stale updates raise the established ASSET_NOT_FOUND response in app/services/tenant_assets.py
- [ ] T055 [US4] Update PATCH /assets/{asset_id} route documentation and OpenAPI examples for marking stale in app/api/routes/assets.py
- [ ] T056 [US4] Add docstrings for any modified stale update handling in app/schemas/assets.py, app/services/tenant_assets.py, and app/api/routes/assets.py

**Checkpoint**: All user stories are independently functional with lifecycle update behavior.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, and cleanup across Phase 4.

- [ ] T057 [P] Update README.md with Phase 4 authentication, import, re-import, partial failure, stale lifecycle, and tenant-isolation evaluator steps in README.md
- [ ] T058 [P] Confirm no new Phase 4 runtime settings are required or document any new required setting in .env.example
- [ ] T059 [P] Add or update concise docstrings for all modified Python functions, class methods, services, repositories, routes, and validators in app/
- [ ] T060 [P] Review import response payloads for bounded summary size and stable created, updated, failed, and errors fields in app/services/tenant_assets.py and app/schemas/assets.py
- [ ] T061 Run quickstart validation steps from specs/004-bulk-import-lifecycle/quickstart.md
- [ ] T062 Run `uv run pytest tests/unit/test_asset_normalization.py`
- [ ] T063 Run `uv run pytest tests/contract/test_assets_api.py`
- [ ] T064 Run `uv run pytest tests/integration/test_asset_import_lifecycle.py tests/integration/test_asset_crud.py tests/integration/test_asset_rbac.py tests/integration/test_asset_tenant_isolation.py`
- [ ] T065 Run `uv run pytest tests/contract tests/integration tests/unit`
- [ ] T066 Run `uv run pytest` against the full tests/ suite
- [ ] T067 Run `uv run ruff check .` using configuration in pyproject.toml
- [ ] T068 Run `uv run mypy app` against the app/ package

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP delivery.
- **User Story 2 (Phase 4)**: Depends on Foundational and builds on US1 import update paths.
- **User Story 3 (Phase 5)**: Depends on Foundational and should be validated against US1 and US2 import behavior.
- **User Story 4 (Phase 6)**: Depends on existing Phase 3 PATCH behavior and US2 stale reactivation behavior.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Import Assets Idempotently**: MVP, no story dependency after Foundation.
- **US2 Refresh Existing Asset Observations**: Depends on US1 import orchestration for update paths.
- **US3 Report Partial Import Failures**: Can start after Foundation, but final validation depends on US1 and US2 processing behavior.
- **US4 Mark Assets Stale Through Asset Update**: Can start from existing PATCH behavior, with final reactivation validation depending on US2.

### Within Each User Story

- Write tests first and verify they fail before implementation.
- Schemas and route contracts before route implementation.
- Repository helpers before service orchestration.
- Service validation, RBAC, tenant scoping, and error mapping before route wiring.
- Story complete before moving to lower-priority work unless tasks are explicitly parallel.

## Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T005 and T006 can run in parallel because schemas and contract tests touch different files.
- T007 and T008 can run in parallel with T009 and T010 once schema names are known.
- US1 tests T014-T018 can run in parallel before implementation.
- US2 tests T024-T029 can run in parallel before implementation.
- US3 tests T036-T040 can run in parallel before implementation.
- US4 tests T047-T051 can run in parallel before implementation.
- Documentation, environment, docstring, and response-size checks T057-T060 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T014 [P] [US1] Add contract tests for POST /assets/import success response shape, created counts, updated counts, and stable summary fields in tests/contract/test_assets_api.py"
Task: "T015 [P] [US1] Add integration tests for first import creating organization-owned assets through POST /assets/import in tests/integration/test_asset_import_lifecycle.py"
Task: "T016 [P] [US1] Add integration tests proving re-importing the same dataset does not increase organization asset count in tests/integration/test_asset_import_lifecycle.py"
Task: "T018 [P] [US1] Add integration tests proving same type and value imports remain independent across two organizations in tests/integration/test_asset_tenant_isolation.py"
```

## Parallel Example: User Story 2

```bash
Task: "T024 [P] [US2] Add integration tests for first_seen preservation and server-owned last_seen refresh on re-import in tests/integration/test_asset_import_lifecycle.py"
Task: "T025 [P] [US2] Add integration tests for ordered tag merge without duplicate tag values in tests/integration/test_asset_import_lifecycle.py"
Task: "T026 [P] [US2] Add integration tests for shallow metadata merge preserving non-conflicting keys and replacing conflicting keys in tests/integration/test_asset_import_lifecycle.py"
Task: "T029 [P] [US2] Add unit tests for tag merge, metadata merge, and lifecycle transition helpers in tests/unit/test_asset_normalization.py"
```

## Parallel Example: User Story 3

```bash
Task: "T036 [P] [US3] Add contract tests for HTTP 207 and HTTP 422 AssetImportSummary response shape in tests/contract/test_assets_api.py"
Task: "T037 [P] [US3] Add integration tests for mixed valid, missing value, blank value, unsupported type, and unsupported status records returning HTTP 207 in tests/integration/test_asset_import_lifecycle.py"
Task: "T038 [P] [US3] Add integration tests for all-record failure returning HTTP 422 without creating or updating assets in tests/integration/test_asset_import_lifecycle.py"
Task: "T040 [P] [US3] Add integration tests proving per-record import errors do not reveal cross-tenant asset data in tests/integration/test_asset_tenant_isolation.py"
```

## Parallel Example: User Story 4

```bash
Task: "T047 [P] [US4] Add contract tests documenting PATCH /assets/{asset_id} with status stale and 403/404 responses in tests/contract/test_assets_api.py"
Task: "T048 [P] [US4] Add integration tests for analyst and admin stale status updates through PATCH /assets/{asset_id} in tests/integration/test_asset_crud.py"
Task: "T049 [P] [US4] Add integration tests for viewer stale update denial and analyst/admin permission boundaries in tests/integration/test_asset_rbac.py"
Task: "T050 [P] [US4] Add integration tests for cross-organization stale update returning ASSET_NOT_FOUND in tests/integration/test_asset_tenant_isolation.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup checks and shared import test scaffolding.
2. Complete Phase 2 shared import schemas, repository helpers, service helpers, and contract documentation.
3. Complete Phase 3 User Story 1 to deliver idempotent POST /assets/import for valid batches.
4. Stop and validate User Story 1 independently with T014-T023.
5. Add User Story 2 lifecycle refresh behavior for timestamps, tags, metadata, stale assets, and archived assets.
6. Add User Story 3 partial and all-record failure behavior.
7. Finish User Story 4 stale marking through PATCH /assets/{asset_id}.

### Incremental Delivery

- Deliver P1 stories first: US1, US2, and US3.
- Treat US4 as the P2 lifecycle complement after core import behavior is stable.
- Run story-specific tests before broader validation commands.
- Use quickstart.md as the final evaluator-facing verification path.

### Notes

- [P] tasks use separate files or can be executed independently.
- [US1], [US2], [US3], and [US4] labels map directly to spec.md user stories.
- Every route, service, repository, and schema task must preserve tenant scoping and avoid client-supplied organization ownership.
- Relationship APIs, graph retrieval, rate limiting, caching, CI expansion, and AI analysis remain out of Phase 4 scope.
