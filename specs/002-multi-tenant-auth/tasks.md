# Tasks: Multi-Tenant Auth

**Input**: Design documents from `/specs/002-multi-tenant-auth/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-api.yaml, quickstart.md

**Tests**: Required by FR-037 and the constitution. Write story tests before implementation and verify they fail for missing behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. All task descriptions include exact target paths.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks
- **[Story]**: User story label for traceability
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Phase 2 dependencies, folders, configuration placeholders, and migration scaffolding.

- [ ] T001 Add `python-jose[cryptography]` and `passlib[bcrypt]` runtime dependencies in `pyproject.toml`
- [ ] T002 Run dependency resolution and update `uv.lock`
- [ ] T003 [P] Create Phase 2 test directories `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T004 [P] Create seed script placeholder in `scripts/seed.py`
- [ ] T005 [P] Create auth route module placeholder in `app/api/routes/auth.py`
- [ ] T006 [P] Create auth schema module placeholder in `app/schemas/auth.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database, security, error, and dependency primitives that MUST be complete before user story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 Create SQLAlchemy timestamp and UUID conventions for Phase 2 models in `app/models/__init__.py`
- [ ] T008 [P] Add auth and token configuration fields in `app/core/config.py`
- [ ] T009 [P] Add JWT password hashing and refresh token hashing helpers in `app/core/security.py`
- [ ] T010 [P] Add structured authentication, authorization, duplicate, and not-found errors in `app/core/errors.py`
- [ ] T011 Create Alembic migration for organizations, users, refresh_tokens, assets, and asset_relationships in `alembic/versions/002_multi_tenant_auth.py`
- [ ] T012 Register all Phase 2 SQLAlchemy models with Alembic metadata in `app/db/base.py`
- [ ] T013 [P] Update `.env.example` with `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_EXPIRE_DAYS`
- [ ] T014 [P] Add shared async test database/session fixtures for Phase 2 tests in `tests/conftest.py`
- [ ] T015 Include `app.api.routes.auth` in the FastAPI router setup in `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Seed Evaluation Tenants and Users (Priority: P1) MVP

**Goal**: Seed two evaluation organizations and four known users without duplicates.

**Independent Test**: Run `uv run python scripts/seed.py` twice, then verify both organizations and exactly four seeded users exist with one organization and one role each.

### Tests for User Story 1

- [ ] T016 [P] [US1] Add seed idempotency integration tests in `tests/integration/test_seed.py`
- [ ] T017 [P] [US1] Add seeded user ownership and role integrity tests in `tests/integration/test_seed.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement `Organization` model in `app/models/organization.py`
- [ ] T019 [P] [US1] Implement `User` model and role constraints in `app/models/user.py`
- [ ] T020 [P] [US1] Implement organization repository helpers in `app/repositories/organizations.py`
- [ ] T021 [P] [US1] Implement user repository helpers in `app/repositories/users.py`
- [ ] T022 [US1] Implement idempotent organization and user seeding in `scripts/seed.py`
- [ ] T023 [US1] Hash seeded user passwords with `app/core/security.py` in `scripts/seed.py`
- [ ] T024 [US1] Document seed command and seeded credentials in `README.md`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Authenticate Seeded Users (Priority: P1)

**Goal**: Seeded active users can log in, inspect identity, refresh with rotation, and log out.

**Independent Test**: Log in with a seeded user, call `/auth/me`, refresh the session, confirm the old refresh token is rejected, then log out and confirm the replacement token is rejected.

### Tests for User Story 2

- [ ] T025 [P] [US2] Add OpenAPI contract tests for `/auth/login`, `/auth/refresh`, `/auth/logout`, and `/auth/me` in `tests/contract/test_auth_api.py`
- [ ] T026 [P] [US2] Add end-to-end login, current-user, refresh rotation, and logout tests in `tests/integration/test_auth_flow.py`
- [ ] T027 [P] [US2] Add security unit tests for password hashing, JWT claims, token expiry, refresh token hashing, and no raw refresh-token log leakage in `tests/unit/test_security.py`
- [ ] T028 [P] [US2] Add token service tests for expired, revoked, malformed, unknown, and reused refresh tokens in `tests/unit/test_token_service.py`

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement `RefreshToken` model in `app/models/refresh_token.py`
- [ ] T030 [P] [US2] Implement auth request and response schemas in `app/schemas/auth.py`
- [ ] T031 [P] [US2] Implement auth repository methods for users and refresh tokens in `app/repositories/auth.py`
- [ ] T032 [US2] Implement credential validation, access token creation, refresh rotation, and logout revocation in `app/services/auth.py`
- [ ] T033 [US2] Implement authenticated user dependency and access-token validation in `app/api/deps.py`
- [ ] T034 [US2] Implement `/auth/login`, `/auth/refresh`, `/auth/logout`, and `/auth/me` handlers in `app/api/routes/auth.py`
- [ ] T035 [US2] Ensure inactive users and invalid credentials return generic authentication failures in `app/services/auth.py`
- [ ] T036 [US2] Document auth flow and absence of public registration, organization creation, and organization switching in `README.md`

**Checkpoint**: User Story 2 is fully functional and testable independently.

---

## Phase 5: User Story 3 - Enforce Tenant Ownership (Priority: P1)

**Goal**: Tenant-owned asset and relationship operations are always scoped to the authenticated organization.

**Independent Test**: Prepare assets in two organizations, verify same type/value can exist in both, verify cross-organization asset access returns 404, and verify cross-organization relationships are rejected.

### Tests for User Story 3

- [ ] T037 [P] [US3] Add tenant-scoped asset and duplicate-value integration tests in `tests/integration/test_tenant_isolation.py`
- [ ] T038 [P] [US3] Add cross-organization asset 404 and relationship rejection tests in `tests/integration/test_tenant_isolation.py`

### Implementation for User Story 3

- [ ] T039 [P] [US3] Implement `Asset` model with organization-scoped uniqueness in `app/models/asset.py`
- [ ] T040 [P] [US3] Implement `AssetRelationship` model with same-organization constraints in `app/models/asset.py`
- [ ] T041 [P] [US3] Implement tenant-scoped asset and relationship repository methods in `app/repositories/assets.py` and `app/repositories/relationships.py`
- [ ] T042 [US3] Implement tenant asset ownership and cross-tenant 404 checks in `app/services/tenant_assets.py`
- [ ] T043 [US3] Implement same-organization relationship validation in `app/services/tenant_assets.py`
- [ ] T044 [US3] Ensure protected dependencies derive organization ownership only from authenticated context in `app/api/deps.py`

**Checkpoint**: User Story 3 is fully functional and testable independently.

---

## Phase 6: User Story 4 - Apply Role-Based Access (Priority: P1)

**Goal**: Viewer, analyst, and admin permissions are enforced through reusable dependencies and services.

**Independent Test**: Authenticate as each seeded role and verify reusable RBAC decisions for read, write, import, stale-marking, relationship creation, and delete/archive operation categories match the role matrix. Phase 2 validates shared helpers and protected ownership checks; full asset CRUD, import, graph, and lifecycle endpoints remain later phases.

### Tests for User Story 4

- [ ] T045 [P] [US4] Add role matrix integration tests for viewer, analyst, and admin permissions in `tests/integration/test_rbac.py`
- [ ] T046 [P] [US4] Add reusable RBAC service unit tests in `tests/unit/test_rbac.py`

### Implementation for User Story 4

- [ ] T047 [P] [US4] Implement role permission enum and action mapping for Phase 2 checks plus later asset CRUD, import, graph, lifecycle, and relationship operation categories in `app/services/rbac.py`
- [ ] T048 [US4] Implement reusable FastAPI role dependency helpers in `app/api/deps.py`
- [ ] T049 [US4] Wire RBAC checks into Phase 2 tenant asset and relationship ownership checks in `app/services/tenant_assets.py`
- [ ] T050 [US4] Ensure forbidden actions return structured authorization failures in `app/core/errors.py`
- [ ] T051 [US4] Document the viewer, analyst, and admin role matrix in `README.md`

**Checkpoint**: User Story 4 is fully functional and testable independently.

---

## Phase 7: User Story 5 - Establish Tenant-Owned Inventory Records (Priority: P2)

**Goal**: Database records, constraints, and indexes support future asset CRUD and graph work.

**Independent Test**: Apply migrations and verify organization, user, refresh token, asset, and relationship tables, ownership links, uniqueness constraints, and indexed lookup paths exist.

### Tests for User Story 5

- [ ] T052 [P] [US5] Add migration schema tests for Phase 2 tables and indexes in `tests/integration/test_schema.py`
- [ ] T053 [P] [US5] Add data-integrity tests for unique emails, slugs, assets, and relationships in `tests/integration/test_schema.py`

### Implementation for User Story 5

- [ ] T054 [US5] Add database check constraints for user roles, asset types, asset statuses, and relationship types in `alembic/versions/002_multi_tenant_auth.py`
- [ ] T055 [US5] Add lookup indexes for email, organization ownership, refresh token owner, asset lookup, and relationship lookup in `alembic/versions/002_multi_tenant_auth.py`
- [ ] T056 [US5] Ensure SQLAlchemy model constraints match migration constraints in `app/models/organization.py`, `app/models/user.py`, `app/models/refresh_token.py`, and `app/models/asset.py`
- [ ] T057 [US5] Verify Alembic autogenerate has no unexpected Phase 2 drift in `alembic/env.py`

**Checkpoint**: User Story 5 is fully functional and testable independently.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, and cleanup across the complete Phase 2 slice.

- [ ] T058 [P] Update `README.md` with migration, seed, auth flow, tenant isolation, role permissions, and Phase 2 scope notes
- [ ] T059 [P] Update `specs/002-multi-tenant-auth/quickstart.md` if implementation commands differ from the planned commands
- [ ] T060 [P] Review `.env.example` for safe placeholders and no committed secrets
- [ ] T061 Run `uv run alembic upgrade head` and document any failure in `specs/002-multi-tenant-auth/quickstart.md`
- [ ] T062 Run `uv run python scripts/seed.py` twice and document any failure in `specs/002-multi-tenant-auth/quickstart.md`
- [ ] T063 Run `uv run pytest tests/contract tests/integration tests/unit`
- [ ] T064 Run `uv run ruff check .`
- [ ] T065 Run `uv run mypy app`
- [ ] T066 Run `uv run pytest`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Stories 1-4 (P1)**: Depend on Foundational completion. US1 seeds data needed by US2, US3, and US4 validation. US2 auth context is needed by US3 and US4 protected checks.
- **User Story 5 (P2)**: Depends on Foundational completion and can be completed alongside P1 stories after shared models and migrations are introduced.
- **Polish**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: Can start after Phase 2; provides seeded organizations and users.
- **US2**: Depends on US1 seeded users for end-to-end validation.
- **US3**: Depends on US2 authenticated context and Phase 2 asset models.
- **US4**: Depends on US2 authenticated context and can validate decisions with seeded roles from US1.
- **US5**: Can run after Phase 2 and should be reconciled before final verification.

### Within Each User Story

- Tests before implementation.
- Models before repositories and services.
- Repositories before services.
- Services before routes and dependencies.
- Documentation after behavior is implemented.

---

## Parallel Execution Examples

### User Story 1

```bash
Task: T016 in tests/integration/test_seed.py
Task: T018 in app/models/organization.py
Task: T019 in app/models/user.py
Task: T020 in app/repositories/organizations.py
Task: T021 in app/repositories/users.py
```

### User Story 2

```bash
Task: T025 in tests/contract/test_auth_api.py
Task: T027 in tests/unit/test_security.py
Task: T028 in tests/unit/test_token_service.py
Task: T029 in app/models/refresh_token.py
Task: T030 in app/schemas/auth.py
Task: T031 in app/repositories/auth.py
```

### User Story 3

```bash
Task: T037 in tests/integration/test_tenant_isolation.py
Task: T039 in app/models/asset.py
Task: T041 in app/repositories/assets.py
Task: T041 in app/repositories/relationships.py
```

### User Story 4

```bash
Task: T045 in tests/integration/test_rbac.py
Task: T046 in tests/unit/test_rbac.py
Task: T047 in app/services/rbac.py
```

### User Story 5

```bash
Task: T052 in tests/integration/test_schema.py
Task: T053 in tests/integration/test_schema.py
Task: T054 in alembic/versions/002_multi_tenant_auth.py
Task: T055 in alembic/versions/002_multi_tenant_auth.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 to establish seeded tenants and users.
3. Validate User Story 1 independently with `tests/integration/test_seed.py`.
4. Complete User Story 2 to establish usable authentication.
5. Continue through P1 stories US3 and US4 before P2 hardening in US5.

### Incremental Delivery

1. Deliver seed data foundation (US1).
2. Deliver auth/session endpoints (US2).
3. Deliver tenant isolation checks (US3).
4. Deliver reusable RBAC helpers (US4).
5. Reconcile schema constraints and indexes (US5).
6. Run final quality gates from quickstart.

### Notes

- [P] tasks are safe to execute in parallel when they touch different files.
- Every user story has an independent test criterion and test tasks.
- Client-supplied organization ownership remains out of scope and must be rejected wherever tenant-owned data is handled.
