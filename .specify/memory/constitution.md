<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template principle 1 -> I. Tenant Isolation Is Mandatory
- Template principle 2 -> II. Security-Sensitive Defaults
- Template principle 3 -> III. Testable Spec-Driven Delivery
- Template principle 4 -> IV. Asset Lifecycle Integrity
- Template principle 5 -> V. Operational Reproducibility
Added sections:
- Backend Architecture Constraints
- Delivery Workflow and Quality Gates
Removed sections:
- Placeholder template guidance
Templates requiring updates:
- .specify/templates/plan-template.md: updated
- .specify/templates/spec-template.md: updated
- .specify/templates/tasks-template.md: updated
- .specify/templates/checklist-template.md: reviewed, no update required
- .specify/templates/commands/*.md: not present
Follow-up TODOs:
- None
-->
# Buguard Asset Management Constitution

## Core Principles

### I. Tenant Isolation Is Mandatory
All tenant-owned resources MUST be scoped by the authenticated user's active
organization. APIs MUST NOT accept `organization_id` from client input for
tenant-owned data. Queries, mutations, imports, relationship creation, graph
retrieval, caches, and AI analysis inputs MUST include organization scoping.

Rationale: The system stores attack-surface inventory for multiple
organizations. Cross-tenant leakage is a critical security failure.

### II. Security-Sensitive Defaults
Authentication, authorization, token handling, and configuration MUST default to
safe behavior. Passwords and refresh tokens MUST be hashed before storage.
Access tokens MUST be short-lived and include user id, organization id, role,
and expiry. Secrets MUST be loaded from environment variables and MUST NOT be
committed. Role checks MUST enforce viewer, analyst, and admin permissions at
the API boundary and service layer where appropriate.

Rationale: Asset management data is security-sensitive, and unsafe defaults are
expensive to correct after implementation.

### III. Testable Spec-Driven Delivery
Every phase MUST be driven by Spec Kit artifacts derived from `PLAN.md`.
Implementation tasks MUST map to user stories, acceptance criteria, and exact
file paths. Behavior that affects data integrity, RBAC, tenant isolation,
imports, graph relationships, refresh tokens, rate limiting, or AI grounding
MUST have automated tests. Tests SHOULD be written before implementation for
new behavior and MUST pass before a phase is considered complete.

Rationale: The project is an assessment of production engineering judgment, not
only endpoint completion.

### IV. Asset Lifecycle Integrity
Asset ingestion and mutation MUST preserve inventory truth. Assets MUST be
deduplicated by organization, type, and canonical value. Imports MUST preserve
`first_seen`, update `last_seen`, merge tags without duplicates, merge metadata
predictably, reactivate stale assets when re-sighted, and report malformed
records without failing the entire batch.

Rationale: Attack-surface management depends on accurate lifecycle history and
idempotent ingestion.

### V. Operational Reproducibility
The backend MUST run consistently through local `uv` commands and Docker
Compose. Required environment variables MUST be documented in `.env.example`.
Database migrations, health checks, linting, tests, and CI commands MUST be
kept current as implementation evolves. Optional services such as Redis or LLM
providers MUST degrade gracefully when not configured.

Rationale: Evaluators and maintainers must be able to boot, test, and inspect
the project from a clean checkout.

## Backend Architecture Constraints

The project targets a production-minded FastAPI backend using PostgreSQL,
SQLAlchemy 2.0, Alembic, Pydantic v2, uv, pytest, Docker Compose, and GitHub
Actions. API code MUST keep route, schema, service, repository, model, and
configuration concerns separated unless a feature is intentionally small enough
to justify a simpler path in the plan.

Structured errors MUST be used for domain failures such as missing assets,
forbidden actions, duplicate relationships, and invalid lifecycle transitions.
Caching, rate limiting, and AI analysis MUST never bypass tenant scoping.

## Delivery Workflow and Quality Gates

Each phase MUST follow the Spec Kit flow in `PLAN.md`: specify, clarify where
needed, checklist, plan, tasks, analyze, implement, test, and commit. A phase is
not complete until its acceptance criteria are satisfied, relevant README notes
are updated, no secrets are committed, and local verification commands for that
phase have passed or failures are explicitly documented.

Generated plans MUST include a Constitution Check covering tenant isolation,
security defaults, tests, lifecycle integrity where relevant, and operational
reproducibility. Generated task lists MUST include setup, tests, implementation,
documentation, and verification tasks at the appropriate phase scope.

## Governance

This constitution supersedes conflicting informal practices for this repository.
Amendments MUST update this file and review dependent Spec Kit templates for
alignment. Versioning follows semantic versioning:

- MAJOR for incompatible governance changes or principle removals.
- MINOR for new principles, new required sections, or materially expanded
  compliance expectations.
- PATCH for clarifications, wording fixes, and non-semantic corrections.

Compliance MUST be reviewed during planning and before phase completion. Any
intentional violation MUST be documented in the feature plan's Complexity
Tracking table with the simpler alternative considered and the reason it was
rejected.

**Version**: 1.0.0 | **Ratified**: 2026-06-25 | **Last Amended**: 2026-06-25
