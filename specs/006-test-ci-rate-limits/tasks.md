# Tasks: Test CI Rate Limits

**Input**: Design documents from `/specs/006-test-ci-rate-limits/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/test-ci-rate-limits-api.yaml, quickstart.md

**Tests**: Tests are required by the specification and constitution for health checks, seeded authentication, refresh tokens, RBAC, tenant isolation, asset CRUD, filtering, sorting, pagination, bulk import, lifecycle handling, relationships, graph retrieval, structured errors, rate limits, cache isolation, cache invalidation, cache fallback, and CI behavior. Write tests first and verify they fail before implementation when adding new behavior.

**Code Documentation**: Add concise docstrings to all new or modified Python functions, class methods, service methods, repository methods, route handlers, and test helpers.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete work
- **[Story]**: Maps the task to a user story from spec.md
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Phase 6 starts from the established FastAPI, auth, asset, import, relationship, graph, test, and documentation foundations.

- [ ] T001 Verify Phase 6 scope, contract, and quickstart alignment in specs/006-test-ci-rate-limits/plan.md, specs/006-test-ci-rate-limits/spec.md, specs/006-test-ci-rate-limits/contracts/test-ci-rate-limits-api.yaml, and specs/006-test-ci-rate-limits/quickstart.md
- [ ] T002 [P] Audit existing auth route, token service, refresh-token repository, dependency injection, and structured errors in app/api/routes/auth.py, app/services/auth.py, app/repositories/auth.py, app/api/deps.py, and app/core/errors.py
- [ ] T003 [P] Audit existing asset list, import, relationship, graph, RBAC, tenant-safety, and write paths in app/api/routes/assets.py, app/services/tenant_assets.py, app/repositories/assets.py, app/repositories/relationships.py, and app/services/rbac.py
- [ ] T004 [P] Audit existing pytest fixtures, seeded users, organization helpers, and HTTP client setup in tests/conftest.py, tests/integration/test_seed.py, tests/integration/test_auth_flow.py, and tests/integration/test_tenant_isolation.py
- [ ] T005 [P] Audit existing project quality configuration and local setup docs in pyproject.toml, README.md, .env.example, docker-compose.yml, and uv.lock

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared rate-limit, cache, configuration, structured-error, and test-helper infrastructure needed before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 [P] Add cache and rate-limit settings with validation and docstrings in app/core/config.py
- [ ] T007 [P] Add RateLimitExceededError using the established structured error envelope and 429 status in app/core/errors.py
- [ ] T008 [P] Add a reusable rate-limit service with operation rules, effective-caller key construction, fixed-window counters, retry metadata, cache-store fallback behavior, and docstrings in app/services/rate_limits.py
- [ ] T009 [P] Add a reusable cache service with organization-scoped key building, JSON serialization, namespace invalidation, graceful fallback, and docstrings in app/services/cache.py
- [ ] T010 [P] Add and lock the selected Redis-compatible cache client dependency in pyproject.toml and uv.lock, then add a cache client dependency provider that can be unavailable without breaking application startup in app/api/deps.py
- [ ] T011 [P] Add reusable test fixtures for seeded user clients, second-organization data, rate-limit windows, and cache stubs in tests/conftest.py
- [ ] T012 [P] Add contract-test helpers for structured 429 responses and cache-related response documentation in tests/contract/test_test_ci_rate_limits_api.py
- [ ] T013 [P] Add unit test modules for rate-limit and cache helper behavior in tests/unit/test_rate_limits.py and tests/unit/test_cache.py
- [ ] T014 [P] Add concise docstrings to new foundation code in app/services/rate_limits.py, app/services/cache.py, app/api/deps.py, app/core/config.py, and app/core/errors.py

**Checkpoint**: Rate-limit, cache, configuration, structured-error, and test foundations are ready for story implementation.

---

## Phase 3: User Story 1 - Verify Core Asset Management Behavior (Priority: P1) MVP

**Goal**: Comprehensive automated tests protect authentication, tenant isolation, RBAC, asset lifecycle, imports, relationships, graph behavior, and structured errors.

**Independent Test**: Run `uv run pytest` from a clean project setup and verify the suite covers health, seeded auth, refresh tokens, RBAC, tenant isolation, asset CRUD, filters, sorting, pagination, bulk import, deduplication, lifecycle handling, relationships, graph retrieval, and structured errors.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add or extend health and startup regression tests in tests/test_health.py and tests/integration/test_schema.py
- [ ] T016 [P] [US1] Add or extend seeded-user and authentication regression tests for admin, analyst, viewer, and second-organization users in tests/integration/test_seed.py and tests/integration/test_auth_flow.py
- [ ] T017 [P] [US1] Add or extend refresh token, logout where present, invalid credential, and structured authentication error tests in tests/contract/test_auth_api.py and tests/integration/test_auth_flow.py
- [ ] T018 [P] [US1] Add or extend viewer, analyst, and admin RBAC regression tests across protected operations in tests/integration/test_rbac.py and tests/integration/test_asset_rbac.py
- [ ] T019 [P] [US1] Add or extend tenant-isolation tests for cross-organization reads, writes, imports, relationships, graph retrieval, and missing-resource non-disclosure in tests/integration/test_tenant_isolation.py and tests/integration/test_asset_tenant_isolation.py
- [ ] T020 [P] [US1] Add or extend asset CRUD, filtering, sorting, pagination, canonical value, and structured validation tests in tests/contract/test_assets_api.py, tests/integration/test_asset_crud.py, and tests/integration/test_asset_filters.py
- [ ] T021 [P] [US1] Add or extend bulk import lifecycle tests for malformed records, partial failures, all-record failures, duplicates, metadata merge, tag merge, stale reactivation, and archived assets in tests/integration/test_asset_import_lifecycle.py
- [ ] T022 [P] [US1] Add or extend relationship and graph tests for duplicate prevention, invalid relationship types, listing, isolated assets, graph shape, and cross-tenant blocking in tests/integration/test_asset_relationships_graph.py and tests/unit/test_asset_relationships.py
- [ ] T023 [P] [US1] Add structured error regression tests for authentication failures, authorization failures, missing resources, invalid input, duplicate relationships, malformed imports, and rate-limit placeholders in tests/contract/test_auth_api.py and tests/contract/test_assets_api.py

### Implementation for User Story 1

- [ ] T024 [US1] Update shared test fixtures to create deterministic overlapping asset values, import batches, relationships, and role-specific clients in tests/conftest.py
- [ ] T025 [US1] Update existing tests to assert structured error envelopes consistently in tests/contract/test_auth_api.py, tests/contract/test_assets_api.py, tests/integration/test_auth_flow.py, and tests/integration/test_asset_import_lifecycle.py
- [ ] T026 [US1] Fix any uncovered Phase 1-5 regressions exposed by the expanded suite in app/api/routes/auth.py, app/api/routes/assets.py, app/services/auth.py, app/services/tenant_assets.py, app/repositories/assets.py, and app/repositories/relationships.py
- [ ] T027 [US1] Add concise docstrings to modified test helpers and touched application functions in tests/conftest.py, app/api/routes/auth.py, app/api/routes/assets.py, app/services/auth.py, and app/services/tenant_assets.py

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Run Continuous Quality Checks (Priority: P1)

**Goal**: Repository changes automatically install locked dependencies, run linting, run tests, and report failing steps on pushed or proposed changes.

**Independent Test**: Open a change that intentionally breaks formatting, linting, or a test, verify the workflow fails, then fix the issue and verify the workflow passes.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add workflow structure tests that verify push and pull_request triggers, uv dependency setup, lint command, pytest command, and named failure-visible steps in tests/integration/test_ci_workflow.py
- [ ] T029 [P] [US2] Add workflow command consistency tests comparing CI commands to documented local commands in tests/integration/test_ci_workflow.py, README.md, and specs/006-test-ci-rate-limits/quickstart.md

### Implementation for User Story 2

- [ ] T030 [US2] Create GitHub Actions quality workflow with checkout, Python 3.13 setup, uv install, locked dependency sync, ruff lint, pytest, and optional mypy steps in .github/workflows/quality.yml
- [ ] T031 [US2] Ensure the workflow fails overall when linting or tests fail and exposes clear step names in .github/workflows/quality.yml
- [ ] T032 [US2] Document the CI validation process and intentional failure check in README.md
- [ ] T033 [US2] Add concise docstrings to any workflow parsing helpers introduced for tests in tests/integration/test_ci_workflow.py

**Checkpoint**: Continuous quality checks are defined and independently verifiable.

---

## Phase 5: User Story 3 - Rate Limit Abuse-Prone Operations (Priority: P1)

**Goal**: Login, refresh, and bulk import requests are limited per trusted effective caller without blocking normal usage below thresholds.

**Independent Test**: Repeatedly call login, refresh, and bulk import above their allowed thresholds and verify structured 429 responses while requests below thresholds keep normal behavior.

### Tests for User Story 3

- [ ] T034 [P] [US3] Add unit tests for rate-limit key construction, thresholds, windows, retry-after calculation, and trusted effective-caller identity in tests/unit/test_rate_limits.py
- [ ] T035 [P] [US3] Add contract tests for /auth/login and /auth/refresh structured 429 response documentation in tests/contract/test_auth_api.py
- [ ] T036 [P] [US3] Add contract tests for /assets/import structured 429 response documentation in tests/contract/test_assets_api.py
- [ ] T037 [P] [US3] Add integration tests proving the 6th login attempt in 60 seconds for the same attempted username plus client network identity returns structured 429 in tests/integration/test_rate_limits.py
- [ ] T038 [P] [US3] Add integration tests proving login attempts below the threshold preserve valid-login and invalid-credential behavior in tests/integration/test_rate_limits.py
- [ ] T039 [P] [US3] Add integration tests proving the 11th refresh attempt in 60 seconds for the same authenticated user plus organization returns structured 429 in tests/integration/test_rate_limits.py
- [ ] T040 [P] [US3] Add integration tests proving the 11th bulk import attempt in 60 seconds for the same authenticated user plus organization returns structured 429 before import processing in tests/integration/test_rate_limits.py
- [ ] T041 [P] [US3] Add integration tests proving client-supplied organization ownership cannot influence refresh or import rate-limit identity in tests/integration/test_rate_limits.py
- [ ] T042 [P] [US3] Add integration tests proving viewer import requests remain forbidden by RBAC independent of import rate limits in tests/integration/test_asset_rbac.py

### Implementation for User Story 3

- [ ] T043 [US3] Implement RateLimitExceededError response details for operation and retry_after_seconds in app/core/errors.py
- [ ] T044 [US3] Implement login rate-limit checks using attempted username plus client network identity before credential verification in app/api/routes/auth.py and app/services/rate_limits.py
- [ ] T045 [US3] Implement refresh rate-limit checks using authenticated refresh-token user plus organization before token rotation in app/api/routes/auth.py, app/services/auth.py, and app/services/rate_limits.py
- [ ] T046 [US3] Implement bulk import rate-limit checks using current_user.id plus current_user.organization_id before import processing in app/api/routes/assets.py and app/services/rate_limits.py
- [ ] T047 [US3] Add operation constants and future ai_analysis policy documentation without adding an AI endpoint in app/services/rate_limits.py
- [ ] T048 [US3] Wire rate-limit configuration defaults and environment overrides for login, refresh, import, future AI, and window seconds in app/core/config.py and .env.example
- [ ] T049 [US3] Add structured 429 response metadata to affected route declarations in app/api/routes/auth.py and app/api/routes/assets.py
- [ ] T050 [US3] Add concise docstrings to modified rate-limit, auth, asset route, auth service, configuration, and error code paths in app/services/rate_limits.py, app/api/routes/auth.py, app/api/routes/assets.py, app/services/auth.py, app/core/config.py, and app/core/errors.py

**Checkpoint**: Login, refresh, and import rate limits are independently functional and tenant safe.

---

## Phase 6: User Story 4 - Cache Organization-Scoped Reads Safely (Priority: P2)

**Goal**: Asset list and graph reads are cached by authenticated organization and response-affecting inputs, invalidated after relevant writes, and gracefully fall back when cache is unavailable.

**Independent Test**: Read assets or a graph for two organizations with overlapping values, mutate one organization, and verify cached responses never leak another organization's data and refresh after writes.

### Tests for User Story 4

- [ ] T051 [P] [US4] Add unit tests for asset-list cache keys including organization, filters, sort field, sort order, page, and page size in tests/unit/test_cache.py
- [ ] T052 [P] [US4] Add unit tests for graph cache keys including organization, center asset id, namespace version, serialization, invalidation, and fallback behavior in tests/unit/test_cache.py
- [ ] T053 [P] [US4] Add contract tests documenting cache-backed /assets and /assets/{asset_id}/graph behavior without changing response shapes in tests/contract/test_assets_api.py
- [ ] T054 [P] [US4] Add integration tests proving cached asset list reads are isolated across organizations with overlapping asset values in tests/integration/test_cache_behavior.py
- [ ] T055 [P] [US4] Add integration tests proving cached graph reads are isolated across organizations and never return foreign nodes or edges in tests/integration/test_cache_behavior.py
- [ ] T056 [P] [US4] Add integration tests proving asset list and graph caches are invalidated after asset create or refresh, asset update, asset delete or archive, bulk import, relationship create or delete, and marking assets stale in tests/integration/test_cache_behavior.py
- [ ] T057 [P] [US4] Add integration tests proving asset list and graph reads return correct uncached organization-scoped results when the cache service is unavailable or returns invalid data in tests/integration/test_cache_behavior.py
- [ ] T058 [P] [US4] Add integration tests proving valid database writes still succeed when cache invalidation cannot reach the cache service in tests/integration/test_cache_behavior.py

### Implementation for User Story 4

- [ ] T059 [US4] Implement cache key builders and namespace invalidation helpers for asset_list and asset_graph responses in app/services/cache.py
- [ ] T060 [US4] Wrap organization-scoped asset listing with cache get, set, and graceful fallback using authenticated organization and all response-affecting query inputs in app/services/tenant_assets.py
- [ ] T061 [US4] Wrap organization-scoped graph retrieval with cache get, set, and graceful fallback using authenticated organization and center asset id in app/services/tenant_assets.py
- [ ] T062 [US4] Invalidate organization asset_list and asset_graph cache namespaces after asset create or refresh, asset update, asset delete or archive, bulk import, relationship create or delete, and marking assets stale in app/services/tenant_assets.py
- [ ] T063 [US4] Add cache response and invalidation structured logging that excludes secrets and tenant-owned payloads in app/services/cache.py and app/services/tenant_assets.py
- [ ] T064 [US4] Wire Redis-compatible cache settings and optional connection creation without making cache availability required for startup in app/core/config.py, app/api/deps.py, docker-compose.yml, and .env.example
- [ ] T065 [US4] Add concise docstrings to modified cache, asset service, dependency, configuration, and route helper code in app/services/cache.py, app/services/tenant_assets.py, app/api/deps.py, app/core/config.py, and app/api/routes/assets.py

**Checkpoint**: Cached reads remain tenant scoped, fresh after writes, and correct during cache outages.

---

## Phase 7: User Story 5 - Document Verification and Operational Behavior (Priority: P3)

**Goal**: Evaluators can run tests, understand CI checks, authenticate as seeded users, exercise rate limits, and understand cache scoping, invalidation, and fallback without reverse-engineering the project.

**Independent Test**: Follow project documentation from a clean checkout to run tests, identify the CI workflow, authenticate as seeded users, and observe documented rate-limited and cached behavior.

### Tests for User Story 5

- [ ] T066 [P] [US5] Add documentation consistency tests for local test commands, CI commands, seeded-user expectations, rate-limit thresholds, cache settings, and future AI rate-limit notes in tests/integration/test_documentation.py
- [ ] T067 [P] [US5] Add environment documentation tests proving every new cache and rate-limit runtime key appears in .env.example and README.md in tests/integration/test_documentation.py

### Implementation for User Story 5

- [ ] T068 [US5] Update README local verification instructions for uv sync, Docker Compose services, migrations, seeding, ruff, pytest, and mypy in README.md
- [ ] T069 [US5] Update README CI documentation for GitHub Actions triggers, required checks, and intentional failure validation in README.md
- [ ] T070 [US5] Update README authentication and seeded-user verification notes without adding public registration or organization creation in README.md
- [ ] T071 [US5] Update README rate-limit documentation for login, refresh, bulk import, structured 429 responses, effective caller identity, and future AI analysis policy in README.md
- [ ] T072 [US5] Update README cache documentation for organization scoping, asset-list inputs, graph center identity, invalidation events, and graceful fallback in README.md
- [ ] T073 [US5] Update .env.example with cache and rate-limit keys using safe placeholder values in .env.example

**Checkpoint**: Documentation makes Phase 6 verification reproducible from a clean checkout.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, cleanup, and complete quality gates across Phase 6.

- [ ] T074 [P] Review tenant isolation and trusted identity handling for rate-limit and cache paths in app/services/rate_limits.py, app/services/cache.py, app/services/tenant_assets.py, app/api/routes/auth.py, and app/api/routes/assets.py
- [ ] T075 [P] Review structured error codes, messages, and response metadata for RATE_LIMITED, authentication failures, authorization failures, missing resources, invalid input, duplicate relationships, malformed imports, and cache fallback paths in app/core/errors.py, app/api/routes/auth.py, and app/api/routes/assets.py
- [ ] T076 [P] Review cache invalidation coverage for every relevant write path in app/services/tenant_assets.py
- [ ] T077 [P] Add or update concise docstrings for all modified Python functions, class methods, service methods, repository methods, route handlers, and test helpers in app/ and tests/
- [ ] T078 [P] Run quickstart validation steps from specs/006-test-ci-rate-limits/quickstart.md
- [ ] T079 Run `uv run ruff check app tests`
- [ ] T080 Run `uv run pytest tests/unit/test_rate_limits.py tests/unit/test_cache.py`
- [ ] T081 Run `uv run pytest tests/contract/test_auth_api.py tests/contract/test_assets_api.py tests/contract/test_test_ci_rate_limits_api.py`
- [ ] T082 Run `uv run pytest tests/integration/test_rate_limits.py tests/integration/test_cache_behavior.py tests/integration/test_ci_workflow.py tests/integration/test_documentation.py`
- [ ] T083 Run `uv run pytest`
- [ ] T084 Run `uv run mypy app`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP delivery for regression confidence.
- **User Story 2 (Phase 4)**: Depends on Foundational; can run after US1 tests identify the suite shape.
- **User Story 3 (Phase 5)**: Depends on Foundational; uses structured errors and rate-limit service.
- **User Story 4 (Phase 6)**: Depends on Foundational; should run after current asset and graph behavior is covered by US1.
- **User Story 5 (Phase 7)**: Depends on US2, US3, and US4 behavior being defined.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Verify Core Asset Management Behavior**: MVP, no story dependency after Foundation.
- **US2 Run Continuous Quality Checks**: Can start after Foundation, with documentation alignment after US1 test commands settle.
- **US3 Rate Limit Abuse-Prone Operations**: Can start after Foundation, independent of caching.
- **US4 Cache Organization-Scoped Reads Safely**: Can start after Foundation, but final validation depends on US1 asset and graph fixtures.
- **US5 Document Verification and Operational Behavior**: Depends on CI, rate-limit, and cache behavior being implemented.

### Within Each User Story

- Write tests first and verify they fail before implementation for new behavior.
- Configuration and structured errors before route integration.
- Reusable services before route or domain-service orchestration.
- Tenant-scoped identity and cache-key construction before persistence or cached reads.
- Story complete before moving to lower-priority work unless tasks are explicitly parallel.

## Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001.
- T006, T007, T008, T009, T010, T011, T012, and T013 can run in parallel because they touch separate foundation areas.
- US1 test expansion tasks T015-T023 can run in parallel before implementation fixes.
- US2 workflow and documentation tests T028-T029 can run in parallel before workflow implementation.
- US3 tests T034-T042 can run in parallel before implementation.
- US4 tests T051-T058 can run in parallel before implementation.
- US5 documentation checks T066-T067 can run in parallel before documentation updates.
- Polish reviews T074-T077 can run in parallel once implementation is complete.

## Parallel Example: User Story 1

```bash
Task: "T016 [P] [US1] Add or extend seeded-user and authentication regression tests for admin, analyst, viewer, and second-organization users in tests/integration/test_seed.py and tests/integration/test_auth_flow.py"
Task: "T019 [P] [US1] Add or extend tenant-isolation tests for cross-organization reads, writes, imports, relationships, graph retrieval, and missing-resource non-disclosure in tests/integration/test_tenant_isolation.py and tests/integration/test_asset_tenant_isolation.py"
Task: "T021 [P] [US1] Add or extend bulk import lifecycle tests for malformed records, partial failures, all-record failures, duplicates, metadata merge, tag merge, stale reactivation, and archived assets in tests/integration/test_asset_import_lifecycle.py"
Task: "T022 [P] [US1] Add or extend relationship and graph tests for duplicate prevention, invalid relationship types, listing, isolated assets, graph shape, and cross-tenant blocking in tests/integration/test_asset_relationships_graph.py and tests/unit/test_asset_relationships.py"
```

## Parallel Example: User Story 2

```bash
Task: "T028 [P] [US2] Add workflow structure tests that verify push and pull_request triggers, uv dependency setup, lint command, pytest command, and named failure-visible steps in tests/integration/test_ci_workflow.py"
Task: "T029 [P] [US2] Add workflow command consistency tests comparing CI commands to documented local commands in tests/integration/test_ci_workflow.py, README.md, and specs/006-test-ci-rate-limits/quickstart.md"
```

## Parallel Example: User Story 3

```bash
Task: "T034 [P] [US3] Add unit tests for rate-limit key construction, thresholds, windows, retry-after calculation, and trusted effective-caller identity in tests/unit/test_rate_limits.py"
Task: "T037 [P] [US3] Add integration tests proving the 6th login attempt in 60 seconds for the same attempted username plus client network identity returns structured 429 in tests/integration/test_rate_limits.py"
Task: "T039 [P] [US3] Add integration tests proving the 11th refresh attempt in 60 seconds for the same authenticated user plus organization returns structured 429 in tests/integration/test_rate_limits.py"
Task: "T040 [P] [US3] Add integration tests proving the 11th bulk import attempt in 60 seconds for the same authenticated user plus organization returns structured 429 before import processing in tests/integration/test_rate_limits.py"
```

## Parallel Example: User Story 4

```bash
Task: "T051 [P] [US4] Add unit tests for asset-list cache keys including organization, filters, sort field, sort order, page, and page size in tests/unit/test_cache.py"
Task: "T054 [P] [US4] Add integration tests proving cached asset list reads are isolated across organizations with overlapping asset values in tests/integration/test_cache_behavior.py"
Task: "T056 [P] [US4] Add integration tests proving asset list and graph caches are invalidated after asset create or refresh, asset update, asset delete or archive, bulk import, relationship create or delete, and marking assets stale in tests/integration/test_cache_behavior.py"
Task: "T057 [P] [US4] Add integration tests proving asset list and graph reads return correct uncached organization-scoped results when the cache service is unavailable or returns invalid data in tests/integration/test_cache_behavior.py"
```

## Parallel Example: User Story 5

```bash
Task: "T066 [P] [US5] Add documentation consistency tests for local test commands, CI commands, seeded-user expectations, rate-limit thresholds, cache settings, and future AI rate-limit notes in tests/integration/test_documentation.py"
Task: "T067 [P] [US5] Add environment documentation tests proving every new cache and rate-limit runtime key appears in .env.example and README.md in tests/integration/test_documentation.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate User Story 1 independently with the expanded test suite.
5. Continue with P1 stories for CI and rate limiting.
6. Add P2 caching after core behavior is covered.
7. Finish with P3 documentation and full quickstart validation.

### Incremental Delivery

1. **Regression MVP**: T001-T027 provide the repeatable safety net for existing behavior.
2. **Operational Gate**: T028-T033 enforce linting and tests through CI.
3. **Abuse Protection**: T034-T050 add structured rate limits for login, refresh, and import.
4. **Safe Performance Layer**: T051-T065 add tenant-scoped caching with invalidation and fallback.
5. **Evaluator Readiness**: T066-T084 complete docs, review, and verification.

### Notes

- [P] tasks use different files or can be completed without depending on incomplete work.
- [US1], [US2], [US3], [US4], and [US5] labels map directly to user stories in specs/006-test-ci-rate-limits/spec.md.
- Each user story is independently testable using the criteria in its phase.
- Phase 6 must not add public registration, public organization creation, organization switching, or AI analysis behavior.
