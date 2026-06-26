# Tasks: Backend Foundation

**Input**: Design documents from `/specs/001-backend-foundation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Include tests for `/health`, required configuration failure, Docker health availability, Alembic no-op readiness, linting, and type checking as required by the specification and constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend package: `app/`
- Routes: `app/api/routes/`
- Dependencies: `app/api/deps.py`
- Configuration/security/errors: `app/core/`
- Database setup: `app/db/`
- Models: `app/models/`
- Schemas: `app/schemas/`
- Services: `app/services/`
- Repositories: `app/repositories/`
- Tests: `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python backend project, package structure, and quality tooling baseline.

- [ ] T001 Create backend package directories and `__init__.py` files in app/, app/api/, app/api/routes/, app/core/, app/db/, app/models/, app/repositories/, app/schemas/, app/services/, and tests/
- [ ] T002 Initialize uv Python 3.13 project metadata and dependencies in pyproject.toml
- [ ] T003 Generate dependency lockfile for the configured dependencies in uv.lock
- [ ] T004 [P] Configure Ruff lint settings in pyproject.toml
- [ ] T005 [P] Configure mypy type-check settings for app/ in pyproject.toml
- [ ] T006 [P] Configure pytest and pytest-asyncio settings in pyproject.toml
- [ ] T007 [P] Create Docker image build instructions for the API service in Dockerfile

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared configuration, application, database, routing, and error boundaries required before user-story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T008 Implement sanitized configuration error type in app/core/errors.py
- [ ] T009 Implement Pydantic settings with required `DATABASE_URL` validation in app/core/config.py
- [ ] T010 Implement async SQLAlchemy engine and session factory using settings in app/db/session.py
- [ ] T011 [P] Expose shared SQLAlchemy metadata for future model discovery in app/db/base.py
- [ ] T012 [P] Implement FastAPI dependency for async database sessions in app/api/deps.py
- [ ] T013 Implement FastAPI application creation and router registration in app/main.py
- [ ] T014 [P] Create placeholder security module without Phase 2 auth behavior in app/core/security.py
- [ ] T015 [P] Document safe placeholder database configuration in .env.example

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Verify Backend Availability (Priority: P1) MVP

**Goal**: Start a minimal FastAPI backend and verify `GET /health` returns exactly `{"status":"ok"}`.

**Independent Test**: Start the backend locally and request `/health`; the response body is exactly `{"status":"ok"}` with a successful HTTP status.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Add automated health endpoint test for exact response body in tests/test_health.py
- [ ] T017 [P] [US1] Add OpenAPI contract alignment test for `/health` in tests/test_health.py

### Implementation for User Story 1

- [ ] T018 [US1] Implement health route returning `{"status":"ok"}` in app/api/routes/health.py
- [ ] T019 [US1] Register health router with the application in app/main.py
- [ ] T020 [US1] Verify the local ASGI entry point `app.main:app` works with Uvicorn in app/main.py

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Reproduce the Local Environment (Priority: P1)

**Goal**: Provide documented local and Docker Compose runtime paths that expose the health endpoint from a clean checkout.

**Independent Test**: Follow README setup commands locally and through Docker Compose, then verify `/health` from each path.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US2] Add configuration-missing startup failure test in tests/test_config.py
- [ ] T022 [P] [US2] Add malformed `DATABASE_URL` sanitized failure test in tests/test_config.py

### Implementation for User Story 2

- [ ] T023 [US2] Add API and PostgreSQL services with `DATABASE_URL` wiring in docker-compose.yml
- [ ] T024 [US2] Ensure Docker image starts Uvicorn with `app.main:app` in Dockerfile
- [ ] T025 [US2] Document local install, startup, environment, and health verification commands in README.md
- [ ] T026 [US2] Document Docker Compose startup, default ports, and health verification commands in README.md
- [ ] T027 [US2] Document sanitized missing-configuration behavior in README.md
- [ ] T028 [US2] Verify API-to-PostgreSQL reachability in Docker Compose using app/db/session.py to execute a minimal `SELECT 1` smoke check from the API container and document the result in README.md

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Prepare Database and Migration Foundation (Priority: P2)

**Goal**: Configure async PostgreSQL session scaffolding and Alembic so future models can be migrated without Phase 1 domain tables.

**Independent Test**: With `DATABASE_URL` configured, run the documented Alembic no-op command and confirm it completes before any domain models exist.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US3] Add database session factory configuration test in tests/test_db_session.py
- [ ] T030 [P] [US3] Add Alembic configuration smoke test in tests/test_alembic.py

### Implementation for User Story 3

- [ ] T031 [US3] Initialize Alembic project configuration in alembic.ini
- [ ] T032 [US3] Configure Alembic async environment and metadata import in alembic/env.py
- [ ] T033 [P] [US3] Create Alembic versions directory placeholder in alembic/versions/.gitkeep
- [ ] T034 [US3] Document no-op migration verification command in README.md
- [ ] T035 [US3] Confirm no Phase 2 domain models or placeholder schema migrations are added under app/models/ and alembic/versions/

**Checkpoint**: User Story 3 should be independently verifiable through the migration readiness command.

---

## Phase 6: User Story 4 - Establish Quality Checks (Priority: P2)

**Goal**: Provide automated tests and quality commands so the Phase 1 baseline can be verified before future feature work.

**Independent Test**: Run the documented test, lint, and type-check commands and confirm all pass.

### Tests for User Story 4

- [ ] T036 [P] [US4] Add test package initialization in tests/__init__.py
- [ ] T037 [P] [US4] Add any shared pytest fixtures for app creation and environment isolation in tests/conftest.py

### Implementation for User Story 4

- [ ] T038 [US4] Ensure `uv run pytest` passes with health and configuration tests in tests/
- [ ] T039 [US4] Ensure `uv run ruff check .` passes for app/, tests/, and configuration files in pyproject.toml
- [ ] T040 [US4] Ensure `uv run mypy app` passes for the backend package in app/
- [ ] T041 [US4] Document test, lint, and type-check commands in README.md

**Checkpoint**: All selected user stories should now be independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across the Phase 1 foundation.

- [ ] T042 [P] Align README setup notes with specs/001-backend-foundation/quickstart.md
- [ ] T043 [P] Verify `.env.example` contains placeholders only and no committed secrets in .env.example
- [ ] T044 [P] Verify Phase 1 contract remains limited to `GET /health` in specs/001-backend-foundation/contracts/openapi.yaml
- [ ] T045 Run local quickstart validation and record any deviations in README.md
- [ ] T046 Run Docker Compose quickstart validation, including API-to-PostgreSQL reachability, and record any deviations in README.md
- [ ] T047 Run final quality gate commands from README.md: `uv run pytest`, `uv run ruff check .`, and `uv run mypy app`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion; uses the health endpoint from User Story 1 for runtime verification.
- **User Story 3 (Phase 5)**: Depends on Foundational completion; can proceed after database configuration exists.
- **User Story 4 (Phase 6)**: Depends on relevant testable behavior from User Stories 1-3.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Verify Backend Availability**: Requires Phase 1 and Phase 2 only; this is the MVP.
- **US2 Reproduce the Local Environment**: Requires Phase 1 and Phase 2; Docker health verification depends on US1 route behavior, and Docker database reachability verification depends on the foundational database session scaffold.
- **US3 Prepare Database and Migration Foundation**: Requires Phase 1 and Phase 2; independent of US1 endpoint behavior after configuration exists.
- **US4 Establish Quality Checks**: Requires tests and implementation from US1-US3 to validate the full Phase 1 baseline.

### Within Each User Story

- Tests MUST be written and fail before implementation where new behavior is added.
- Configuration and app setup before route registration.
- Docker and README commands after the local app entry point exists.
- Alembic configuration after database settings and metadata are available.
- Final verification after implementation and documentation are complete.

### Parallel Opportunities

- T004, T005, T006, and T007 can run in parallel after T002.
- T011, T012, T014, and T015 can run in parallel after T009 is defined.
- T016 and T017 can run in parallel before T018.
- T021 and T022 can run in parallel before T023.
- T029, T030, and T033 can run in parallel after the database scaffold exists.
- T036 and T037 can run in parallel with other User Story 4 setup work.
- T042, T043, and T044 can run in parallel during polish.

## Parallel Execution Examples

### User Story 1

```text
Task: "T016 [P] [US1] Add automated health endpoint test for exact response body in tests/test_health.py"
Task: "T017 [P] [US1] Add OpenAPI contract alignment test for `/health` in tests/test_health.py"
```

### User Story 2

```text
Task: "T021 [P] [US2] Add configuration-missing startup failure test in tests/test_config.py"
Task: "T022 [P] [US2] Add malformed `DATABASE_URL` sanitized failure test in tests/test_config.py"
```

### User Story 3

```text
Task: "T029 [P] [US3] Add database session factory configuration test in tests/test_db_session.py"
Task: "T030 [P] [US3] Add Alembic configuration smoke test in tests/test_alembic.py"
Task: "T033 [P] [US3] Create Alembic versions directory placeholder in alembic/versions/.gitkeep"
```

### User Story 4

```text
Task: "T036 [P] [US4] Add test package initialization in tests/__init__.py"
Task: "T037 [P] [US4] Add any shared pytest fixtures for app creation and environment isolation in tests/conftest.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate `/health` independently with `uv run pytest tests/test_health.py`.
5. Continue with User Story 2 for reproducibility, then User Story 3 for database and migrations, then User Story 4 for the full quality gate.

### Incremental Delivery

1. Deliver US1 so evaluators can boot the app and verify availability.
2. Deliver US2 so the same behavior is reproducible from local and Docker paths.
3. Deliver US3 so future domain work has database and migration scaffolding.
4. Deliver US4 so the baseline is protected by tests, linting, and typing.

### Notes

- [P] tasks = different files, no dependencies on incomplete tasks.
- [Story] label maps task to a specific user story for traceability.
- Phase 1 must not add authentication, tenant models, asset models, imports, relationships, rate limiting, caching, CI, or AI analysis behavior.
- Each user story should be independently completable and testable.
