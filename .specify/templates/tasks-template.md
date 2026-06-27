---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories),
research.md, data-model.md, contracts/

**Tests**: Include tests for behavior required by the constitution, especially
tenant isolation, RBAC, security-sensitive flows, lifecycle integrity, imports,
relationships, rate limiting, and AI grounding where relevant.

**Code Documentation**: Include tasks for concise docstrings on all new or
modified Python functions, class methods, and service/repository methods. Avoid
inline comments unless they explain non-obvious logic, assumptions, or important
implementation decisions.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python project with FastAPI/backend dependencies
- [ ] T003 [P] Configure linting, typing, and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework when required
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure structured error handling and logging infrastructure
- [ ] T009 Setup environment configuration management
- [ ] T010 Update `.env.example` with every required runtime key and safe placeholder values

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T012 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py
- [ ] T013 [P] [US1] Tenant isolation/RBAC regression test in tests/integration/test_[name].py

### Implementation for User Story 1

- [ ] T014 [P] [US1] Create [Entity1] model in app/models/[entity1].py
- [ ] T015 [P] [US1] Create [Entity2] model in app/models/[entity2].py
- [ ] T016 [US1] Implement [Repository] in app/repositories/[repository].py
- [ ] T017 [US1] Implement [Service] in app/services/[service].py
- [ ] T018 [US1] Implement schemas in app/schemas/[schema].py
- [ ] T019 [US1] Implement [endpoint/feature] in app/api/routes/[route].py
- [ ] T020 [US1] Add validation, structured errors, and logging

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2

- [ ] T021 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T022 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py
- [ ] T023 [P] [US2] Tenant isolation/RBAC regression test in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create [Entity] model in app/models/[entity].py
- [ ] T025 [US2] Implement [Repository] in app/repositories/[repository].py
- [ ] T026 [US2] Implement [Service] in app/services/[service].py
- [ ] T027 [US2] Implement schemas in app/schemas/[schema].py
- [ ] T028 [US2] Implement [endpoint/feature] in app/api/routes/[route].py
- [ ] T029 [US2] Integrate with User Story 1 components if needed

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3

- [ ] T030 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T031 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T032 [P] [US3] Create [Entity] model in app/models/[entity].py
- [ ] T033 [US3] Implement [Repository] in app/repositories/[repository].py
- [ ] T034 [US3] Implement [Service] in app/services/[service].py
- [ ] T035 [US3] Implement schemas in app/schemas/[schema].py
- [ ] T036 [US3] Implement [endpoint/feature] in app/api/routes/[route].py

**Checkpoint**: All selected user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in README.md or docs/
- [ ] TXXX [P] Add or update concise docstrings for modified Python functions, class methods, services, and repositories
- [ ] TXXX [P] README and `.env.example` updates for new configuration or commands
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation
- [ ] TXXX Run `uv run ruff check .` and `uv run pytest`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests MUST be written and fail before implementation when new behavior is added
- Models before repositories and services
- Repositories before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel within Phase 2
- Tests for a user story marked [P] can run in parallel
- Models and schemas in separate files can run in parallel
- Different user stories can be worked on in parallel after Foundational completion

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate User Story 1 independently
5. Continue by priority

### Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to a specific user story for traceability
- Each user story should be independently completable and testable
- Avoid vague tasks, same-file conflicts, and cross-story dependencies that break independence
