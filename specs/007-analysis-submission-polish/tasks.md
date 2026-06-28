# Tasks: Analysis Submission Polish

**Input**: Design documents from `/specs/007-analysis-submission-polish/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Required by the feature specification for analysis grounding, tenant isolation, provider failure behavior, certificate lifecycle consistency, sample-shaped import compatibility, relationship safety, documentation readiness, and final verification.

**Code Documentation**: Add or update concise docstrings for every new or modified Python function, class method, service method, repository method, and provider method.

**Organization**: Tasks are grouped by user story to keep each story independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete same-file changes
- **[Story]**: User story label from spec.md
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 7 files, configuration placeholders, and route/module scaffolding.

- [ ] T001 Create analysis route module scaffold in app/api/routes/analysis.py
- [ ] T002 [P] Create analysis schema module scaffold in app/schemas/analysis.py
- [ ] T003 [P] Create analysis service module scaffold in app/services/analysis.py
- [ ] T004 [P] Create shared certificate lifecycle service scaffold in app/services/certificate_lifecycle.py
- [ ] T005 [P] Create analysis contract test module in tests/contract/test_analysis_api.py
- [ ] T006 [P] Create Phase 7 integration test modules in tests/integration/test_analysis_report.py, tests/integration/test_asset_certificate_lifecycle.py, tests/integration/test_asset_import_sample_shape.py, and tests/integration/test_submission_documentation.py
- [ ] T007 [P] Create Phase 7 unit test modules in tests/unit/test_analysis_provider.py and tests/unit/test_certificate_lifecycle.py
- [ ] T008 Add analysis provider placeholder settings to .env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core behavior required before any user story can be completed.

**CRITICAL**: No user story is complete until this phase is complete.

- [ ] T009 Add analysis provider, model, timeout, evidence limit, and availability settings to app/core/config.py
- [ ] T010 Add structured analysis unavailable, failed, and grounding error classes in app/core/errors.py
- [ ] T011 Add analysis dependency provider that can be unavailable without breaking application startup in app/api/deps.py
- [ ] T012 Register analysis router in app/main.py
- [ ] T013 Add AI analysis rate-limit constant and policy wiring using existing Phase 6 rate-limit patterns in app/services/rate_limits.py
- [ ] T014 Add parent and covers relationship types to RelationshipType and relationship check constraint in app/models/asset.py
- [ ] T015 Create Alembic migration for parent and covers relationship type constraint updates in alembic/versions/003_phase7_parent_relationship.py
- [ ] T016 [P] Add analysis schemas for filters, evidence assets, risks, completed/no-data reports, and structured statuses in app/schemas/analysis.py
- [ ] T017 [P] Add certificate lifecycle status type and parser helpers in app/services/certificate_lifecycle.py
- [ ] T018 [P] Add asset schema fields for certificate_lifecycle_status and sample import references in app/schemas/assets.py
- [ ] T019 Update asset cache key serialization to include certificate lifecycle filters in app/services/cache.py
- [ ] T020 Add provider interface, configured analysis provider implementation, unavailable provider, fake-test seams, and output validation skeleton in app/services/analysis.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Generate Grounded Inventory Risk Reports (Priority: P1) MVP

**Goal**: Authenticated users can request grounded inventory risk reports based only on filtered assets in their own organization, including certificate lifecycle evidence.

**Independent Test**: Authenticate users from two organizations, request filtered reports, and verify reports contain only matching current-organization evidence IDs, no fabricated no-data output, and correct expired/expiring-soon certificate findings.

### Tests for User Story 1

- [ ] T021 [P] [US1] Add contract tests for POST /analysis/report success, no-data, and evidence response shape in tests/contract/test_analysis_api.py
- [ ] T022 [P] [US1] Add integration tests for authenticated report generation with type, status, tag, source, value_contains, and limit filters in tests/integration/test_analysis_report.py
- [ ] T023 [P] [US1] Add tenant isolation tests proving analysis excludes overlapping assets from other organizations in tests/integration/test_analysis_report.py
- [ ] T024 [P] [US1] Add no-match tests proving reports return no_data with empty evidence and no invented risks in tests/integration/test_analysis_report.py
- [ ] T025 [P] [US1] Add grounded evidence tests rejecting provider risks that reference unselected or cross-tenant asset IDs in tests/integration/test_analysis_report.py
- [ ] T026 [P] [US1] Add certificate analysis tests for expired, expiring_soon, valid future, missing, and malformed metadata.expires in tests/integration/test_analysis_report.py
- [ ] T027 [P] [US1] Add unit tests for provider output normalization and grounding validation in tests/unit/test_analysis_provider.py

### Implementation for User Story 1

- [ ] T028 [US1] Implement analysis filter validation and bounded evidence limit handling in app/schemas/analysis.py
- [ ] T029 [US1] Add organization-scoped evidence selection query supporting analysis filters in app/repositories/assets.py
- [ ] T030 [US1] Implement certificate lifecycle enrichment for evidence assets in app/services/analysis.py
- [ ] T031 [US1] Implement no-data report construction without provider calls in app/services/analysis.py
- [ ] T032 [US1] Implement provider report request construction from selected evidence only in app/services/analysis.py
- [ ] T033 [US1] Implement provider output grounding validation for evidence_asset_ids and risk evidence IDs in app/services/analysis.py
- [ ] T034 [US1] Implement expired and expiring-soon certificate risk enrichment using shared classifier in app/services/analysis.py
- [ ] T035 [US1] Implement authenticated POST /analysis/report endpoint with structured responses in app/api/routes/analysis.py
- [ ] T036 [US1] Apply existing AI analysis rate limit policy to POST /analysis/report in app/api/routes/analysis.py
- [ ] T037 [US1] Add concise docstrings for new analysis callables in app/api/routes/analysis.py, app/services/analysis.py, app/repositories/assets.py, and app/schemas/analysis.py

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Handle Required Analysis Configuration and Failures Safely (Priority: P1)

**Goal**: The analysis endpoint exists even when provider configuration is missing, failures return safe structured errors, and core asset workflows keep working.

**Independent Test**: Run with missing and failing analysis configuration, verify POST /analysis/report returns structured unavailable/failure responses without secrets, and verify normal asset list/import/update/relationship/graph workflows still work.

### Tests for User Story 2

- [ ] T038 [P] [US2] Add contract tests for 503 analysis_unavailable, 502 analysis_failed, and 502 analysis_grounding_failed envelopes in tests/contract/test_analysis_api.py
- [ ] T039 [P] [US2] Add integration tests for missing provider configuration returning structured unavailable responses in tests/integration/test_analysis_report.py
- [ ] T040 [P] [US2] Add integration tests for provider exceptions returning safe failure responses without partial reports or secrets in tests/integration/test_analysis_report.py
- [ ] T041 [P] [US2] Add regression tests proving asset list, import, update, relationships, and graph reads still work while analysis is unavailable in tests/integration/test_analysis_report.py
- [ ] T042 [P] [US2] Add rate-limit tests for POST /analysis/report using the documented AI analysis policy in tests/integration/test_rate_limits.py

### Implementation for User Story 2

- [ ] T043 [US2] Implement safe missing-provider detection and unavailable provider creation in app/api/deps.py
- [ ] T044 [US2] Implement provider failure mapping to structured analysis_failed errors in app/services/analysis.py
- [ ] T045 [US2] Implement grounding failure mapping to structured analysis_grounding_failed errors in app/services/analysis.py
- [ ] T046 [US2] Ensure analysis configuration never raises during app startup when provider settings are absent in app/core/config.py and app/main.py
- [ ] T047 [US2] Ensure analysis errors do not include secrets, raw prompts, provider stack traces, or cross-tenant details in app/core/errors.py and app/services/analysis.py
- [ ] T048 [US2] Add concise docstrings for modified configuration, dependency, and error callables in app/core/config.py, app/api/deps.py, app/core/errors.py, and app/services/analysis.py

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Finalize Submission Documentation (Priority: P1)

**Goal**: Evaluators can start from a clean checkout, configure services, seed users, authenticate, exercise workflows, understand architecture, and verify Phase 7 behavior from documentation.

**Independent Test**: Follow README and .env.example from a clean checkout, seed users, log in, exercise documented workflows, and run documented verification commands.

### Tests for User Story 3

- [ ] T049 [P] [US3] Add documentation tests for required README sections and scope assumptions in tests/integration/test_submission_documentation.py
- [ ] T050 [P] [US3] Add .env.example tests for required database, JWT, cache, rate-limit, and analysis placeholders in tests/integration/test_submission_documentation.py
- [ ] T051 [P] [US3] Add tests proving README command examples mention current test, lint, migration, seed, auth, import, lifecycle, graph, rate-limit, and analysis workflows in tests/integration/test_submission_documentation.py

### Implementation for User Story 3

- [ ] T052 [US3] Update README project overview, architecture summary, feature list, and request documentation pointers in README.md
- [ ] T053 [US3] Update README setup, container startup, migration, seed, seeded credential, and authentication examples in README.md
- [ ] T054 [US3] Update README examples for asset import, sample-shaped records, relationships, graph usage, certificate lifecycle filters, rate limits, and analysis reports in README.md
- [ ] T055 [US3] Update README multi-tenancy, RBAC, deduplication, relationship model, required analysis behavior, certificate lifecycle, known tradeoffs, and future improvements in README.md
- [ ] T056 [US3] Document out-of-scope public registration, public organization creation, organization switching, live scanning, cross-organization reports, and multi-organization membership in README.md
- [ ] T057 [US3] Update .env.example with safe placeholders and comments for all required runtime and analysis configuration values in .env.example
- [ ] T058 [US3] Add final clean-start verification checklist covering startup, seed, login, workflows, tests, linting, and documented exceptions in README.md

**Checkpoint**: User Story 3 is independently verifiable from documentation.

---

## Phase 6: User Story 4 - Import Relationship-Rich Sample Datasets (Priority: P1)

**Goal**: Bulk import accepts evaluator sample-shaped records with import-local IDs, parent and covers references, larger batches, partial success, and malformed record reporting.

**Independent Test**: Import domain a1, subdomain a2 with parent a1, and certificate a3 with covers a2, then verify valid assets import, parent and covers relationships are created inside the authenticated organization, malformed records are reported, and unresolved references do not create unsafe relationships.

### Tests for User Story 4

- [ ] T059 [P] [US4] Add contract tests for sample-shaped POST /assets/import success, partial success 207, and no accepted records 422 in tests/contract/test_assets_api.py
- [ ] T060 [P] [US4] Add integration tests for domain, subdomain parent, and certificate covers sample import in tests/integration/test_asset_import_sample_shape.py
- [ ] T061 [P] [US4] Add integration tests for larger sample-shaped batches with unrelated malformed records and partial success reporting in tests/integration/test_asset_import_sample_shape.py
- [ ] T062 [P] [US4] Add integration tests for missing, invalid, skipped, duplicate, and unsafe relationship references in tests/integration/test_asset_import_sample_shape.py
- [ ] T063 [P] [US4] Add tenant isolation tests proving imported relationship references resolve only within the authenticated organization in tests/integration/test_asset_import_sample_shape.py
- [ ] T064 [P] [US4] Add unit tests for import-local ID collection, duplicate reference handling, parent/covers reference validation, and error reasons in tests/unit/test_asset_relationships.py

### Implementation for User Story 4

- [ ] T065 [US4] Extend import record validation to accept import-local id, parent, and covers while still rejecting organization_id in app/services/tenant_assets.py
- [ ] T066 [US4] Extend AssetImportRecord schema documentation for id, parent, and covers fields in app/schemas/assets.py
- [ ] T067 [US4] Implement two-pass import-local reference collection and processed asset mapping in app/services/tenant_assets.py
- [ ] T068 [US4] Implement parent relationship creation from subdomain source to domain target in app/services/tenant_assets.py
- [ ] T069 [US4] Implement covers relationship creation from certificate source to subdomain target in app/services/tenant_assets.py
- [ ] T070 [US4] Report unresolved, invalid, duplicate, skipped, ambiguous, and unsafe relationship references without creating relationships in app/services/tenant_assets.py
- [ ] T071 [US4] Preserve tags and nested metadata including certificate issuer and expires during sample-shaped imports in app/services/tenant_assets.py
- [ ] T072 [US4] Update relationship repository helpers if needed for idempotent import-created parent and covers relationships in app/repositories/relationships.py
- [ ] T073 [US4] Update relationship enum, schemas, OpenAPI examples, and import summary examples for parent and covers in app/models/asset.py and app/schemas/assets.py
- [ ] T074 [US4] Add concise docstrings for modified import and relationship callables in app/services/tenant_assets.py, app/repositories/relationships.py, and app/schemas/assets.py

**Checkpoint**: User Story 4 is independently functional and sample dataset-compatible.

---

## Phase 7: User Story 5 - Verify Final Submission Readiness (Priority: P2)

**Goal**: Final verification covers clean startup, tests, linting, examples, environment variables, and known tradeoffs.

**Independent Test**: Follow final verification steps from a clean state and confirm documented commands, credentials, workflow examples, and tradeoff notes match current behavior.

### Tests for User Story 5

- [ ] T075 [P] [US5] Add final readiness documentation assertions for verification commands and known tradeoffs in tests/integration/test_submission_documentation.py
- [ ] T076 [P] [US5] Add CI/readiness tests ensuring Phase 7 test modules are discoverable by the documented pytest command in tests/integration/test_ci_workflow.py

### Implementation for User Story 5

- [ ] T077 [US5] Run and reconcile quickstart validation steps from specs/007-analysis-submission-polish/quickstart.md against README.md
- [ ] T078 [US5] Run uv run pytest and document or fix any failures discovered in tests/
- [ ] T079 [US5] Run uv run ruff check . and document or fix any failures discovered in app/ and tests/
- [ ] T080 [US5] Run uv run mypy app tests and document or fix any failures discovered in app/ and tests/
- [ ] T081 [US5] Record final submission tradeoffs and future improvements in README.md

**Checkpoint**: Final submission readiness is documented and verified.

---

## Phase 8: User Story 6 - Review Certificate Lifecycle Outside Analysis (Priority: P2)

**Goal**: Certificate lifecycle status appears consistently in import reporting, asset reads, asset lists, lifecycle filters, graph nodes, documentation, examples, tests, and analysis.

**Independent Test**: Import certificates with expired, expiring-soon, valid future, missing, and malformed metadata.expires values, then verify import reporting, asset read/list responses, lifecycle filters, graph nodes, docs, and analysis use the same classifier.

### Tests for User Story 6

- [ ] T082 [P] [US6] Add unit tests for expired, expiring_soon, valid, unknown missing, and unknown malformed lifecycle classification in tests/unit/test_certificate_lifecycle.py
- [ ] T083 [P] [US6] Add integration tests for malformed certificate metadata.expires import reporting with unrelated valid records preserved in tests/integration/test_asset_certificate_lifecycle.py
- [ ] T084 [P] [US6] Add integration tests for certificate_lifecycle_status on GET /assets/{asset_id} and GET /assets responses in tests/integration/test_asset_certificate_lifecycle.py
- [ ] T085 [P] [US6] Add integration tests for certificate_lifecycle_status filters returning only authenticated-organization certificates in tests/integration/test_asset_certificate_lifecycle.py
- [ ] T086 [P] [US6] Add integration tests for certificate lifecycle status on graph certificate nodes connected through covers relationships in tests/integration/test_asset_certificate_lifecycle.py

### Implementation for User Story 6

- [ ] T087 [US6] Implement shared lifecycle classifier with evaluation-date injection and 30-calendar-day inclusive window in app/services/certificate_lifecycle.py
- [ ] T088 [US6] Enrich AssetRead.from_model with derived certificate_lifecycle_status for certificate assets in app/schemas/assets.py
- [ ] T089 [US6] Enrich GraphAsset.from_model with derived certificate_lifecycle_status for certificate nodes in app/schemas/assets.py
- [ ] T090 [US6] Add certificate_lifecycle_status query parameter handling to list_params in app/api/routes/assets.py
- [ ] T091 [US6] Add certificate lifecycle filter validation to AssetListParams in app/schemas/assets.py
- [ ] T092 [US6] Add organization-scoped certificate lifecycle filtering for expired and expiring_soon assets in app/repositories/assets.py
- [ ] T093 [US6] Add malformed metadata.expires reporting during import without discarding unrelated valid records in app/services/tenant_assets.py
- [ ] T094 [US6] Ensure analysis report evidence and risks call the shared lifecycle classifier rather than analysis-only date logic in app/services/analysis.py
- [ ] T095 [US6] Update README examples for expired, expiring-soon, valid future, missing expiry, and malformed expiry certificate records in README.md
- [ ] T096 [US6] Add concise docstrings for modified lifecycle, asset schema, route, repository, import, graph, and analysis callables in app/services/certificate_lifecycle.py, app/schemas/assets.py, app/api/routes/assets.py, app/repositories/assets.py, app/services/tenant_assets.py, and app/services/analysis.py

**Checkpoint**: Certificate lifecycle behavior is shared and independently verifiable outside analysis.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story consistency, cleanup, and validation.

- [ ] T097 [P] Update specs/007-analysis-submission-polish/quickstart.md if implementation changes final command names, example payloads, or response shapes
- [ ] T098 [P] Update specs/007-analysis-submission-polish/contracts/analysis-report-api.md, specs/007-analysis-submission-polish/contracts/asset-lifecycle-api.md, and specs/007-analysis-submission-polish/contracts/import-sample-api.md if implementation changes API details
- [ ] T099 [P] Review all Phase 7 Python changes for concise docstrings and remove stale inline comments in app/
- [ ] T100 [P] Review OpenAPI tags, summaries, and response models for analysis, assets, import, relationships, and graph in app/api/routes/analysis.py and app/api/routes/assets.py
- [ ] T101 Run uv run pytest tests/contract tests/integration tests/unit and fix Phase 7 regressions in tests/
- [ ] T102 Run uv run ruff check . and fix lint issues in app/ and tests/
- [ ] T103 Run uv run mypy app tests and fix typing issues in app/ and tests/
- [ ] T104 Run alembic upgrade head against a clean database and verify parent/covers relationship constraints in alembic/versions/003_phase7_parent_relationship.py
- [ ] T105 Run the documentation readiness flow from README.md and specs/007-analysis-submission-polish/quickstart.md and update those files if behavior differs
- [ ] T106 Verify all Phase 7 scope exclusions remain unimplemented in README.md, app/api/routes/, and app/services/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks story completion
- **US1 Grounded Analysis (Phase 3)**: Depends on Foundational; MVP scope
- **US2 Analysis Failure Safety (Phase 4)**: Depends on Foundational and can proceed alongside US1 after shared analysis scaffolding exists
- **US3 Documentation (Phase 5)**: Depends on Foundational for config names and can proceed alongside implementation with final reconciliation later
- **US4 Sample Import (Phase 6)**: Depends on Foundational relationship enum/migration work
- **US5 Readiness (Phase 7)**: Depends on desired P1 stories and documentation being complete
- **US6 Lifecycle Outside Analysis (Phase 8)**: Depends on Foundational classifier scaffold and can proceed alongside US1/US4 after classifier contracts are stable
- **Final Polish**: Depends on all selected user stories being complete

### User Story Completion Order

1. **MVP**: US1 - Generate Grounded Inventory Risk Reports
2. **Safety Pair**: US2 - Handle Required Analysis Configuration and Failures Safely
3. **Submission Basics**: US3 - Finalize Submission Documentation
4. **Dataset Compatibility**: US4 - Import Relationship-Rich Sample Datasets
5. **Lifecycle Consistency**: US6 - Review Certificate Lifecycle Outside Analysis
6. **Readiness Sweep**: US5 - Verify Final Submission Readiness

### Within Each User Story

- Tests must be written first and fail before implementation when new behavior is added.
- Schemas and models before repositories and services.
- Repositories before service orchestration.
- Services before route handlers.
- Documentation examples after response shapes are stable.
- Story complete before treating dependent final verification tasks as done.

---

## Parallel Execution Examples

### US1 Parallel Work

```text
Task: T021 [US1] Contract tests in tests/contract/test_analysis_api.py
Task: T022 [US1] Filtered report integration tests in tests/integration/test_analysis_report.py
Task: T027 [US1] Provider validation unit tests in tests/unit/test_analysis_provider.py
Task: T029 [US1] Evidence selection query in app/repositories/assets.py
```

### US2 Parallel Work

```text
Task: T038 [US2] Error envelope contract tests in tests/contract/test_analysis_api.py
Task: T041 [US2] Core workflow regression tests in tests/integration/test_analysis_report.py
Task: T043 [US2] Safe provider dependency in app/api/deps.py
Task: T047 [US2] Safe error content in app/core/errors.py and app/services/analysis.py
```

### US3 Parallel Work

```text
Task: T049 [US3] README section assertions in tests/integration/test_submission_documentation.py
Task: T052 [US3] Overview and architecture docs in README.md
Task: T057 [US3] Environment placeholders in .env.example
```

### US4 Parallel Work

```text
Task: T059 [US4] Import contract tests in tests/contract/test_assets_api.py
Task: T060 [US4] Sample import integration tests in tests/integration/test_asset_import_sample_shape.py
Task: T064 [US4] Import reference unit tests in tests/unit/test_asset_relationships.py
Task: T072 [US4] Relationship repository helpers in app/repositories/relationships.py
```

### US5 Parallel Work

```text
Task: T075 [US5] Readiness documentation assertions in tests/integration/test_submission_documentation.py
Task: T076 [US5] CI/readiness test discovery in tests/integration/test_ci_workflow.py
```

### US6 Parallel Work

```text
Task: T082 [US6] Lifecycle classifier unit tests in tests/unit/test_certificate_lifecycle.py
Task: T083 [US6] Import reporting integration tests in tests/integration/test_asset_certificate_lifecycle.py
Task: T090 [US6] Asset route query parameter in app/api/routes/assets.py
Task: T092 [US6] Lifecycle filtering in app/repositories/assets.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational analysis, relationship, lifecycle, config, and route wiring.
3. Complete Phase 3 US1 for the required grounded analysis report MVP.
4. Validate US1 independently with contract, integration, and unit tests.
5. Complete US2 to harden unavailable/failure behavior.
6. Complete US3 and US4 for final submission documentation and evaluator dataset compatibility.
7. Complete US6 lifecycle consistency and US5 final readiness.
8. Run final polish validation.

### Incremental Delivery

- Deliver US1 as the first demoable increment: authenticated `POST /analysis/report` with organization-scoped evidence, no-data handling, certificate lifecycle risk evidence, and grounded output validation.
- Add US2 immediately after US1 so missing provider configuration and provider failures are safe and evaluator-visible.
- Deliver US4 independently through the existing `/assets/import` endpoint so evaluator datasets load without manual transformation.
- Deliver US6 to unify certificate lifecycle behavior across import, asset reads, filters, graph, and analysis.
- Finish with US3 and US5 documentation and verification reconciliation before final submission.

### Notes

- [P] tasks use different files or are test-only work that can be completed independently.
- [US] labels map directly to user stories in spec.md.
- Phase 7 scope excludes public registration, public organization creation, organization switching, live scanning, cross-organization reports, and multi-organization user membership.
