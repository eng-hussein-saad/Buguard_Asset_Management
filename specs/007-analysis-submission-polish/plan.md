# Implementation Plan: Analysis Submission Polish

**Branch**: `007-analysis-submission-polish` | **Date**: 2026-06-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-analysis-submission-polish/spec.md`

**Note**: This plan covers Phase 7 only: grounded analysis reporting, shared
certificate lifecycle handling, sample-shaped bulk import compatibility, and
final submission polish.

## Summary

Phase 7 finalizes the submission by adding a required authenticated
`/analysis/report` workflow that generates grounded inventory risk reports only
from organization-owned assets, extending certificate lifecycle classification
across import/read/list/filter/graph/analysis surfaces, accepting the evaluator's
sample-shaped import records with import-local relationship references, and
updating final documentation and verification instructions. The implementation
uses the existing FastAPI, Pydantic, service, repository, RBAC, rate-limit, and
tenant-scoped asset patterns, with controlled provider abstraction for analysis
so tests never rely on live external responses.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, asyncpg,
pytest, pytest-asyncio, httpx, ruff, mypy, uv, Docker Compose, Redis-compatible
cache/rate-limit client already introduced for Phase 6, and an environment-driven
analysis provider abstraction.

**Storage**: PostgreSQL via async SQLAlchemy sessions; no new database table is
required for generated reports unless implementation discovers an existing audit
requirement. Relationship type support may require model/schema enum and
migration updates if the relationship type set is database-constrained.

**Testing**: pytest, pytest-asyncio, httpx, controlled fake analysis provider,
unit tests for certificate lifecycle classification, and integration/contract
tests for tenant scoping, import compatibility, graph output, filters, and final
documentation.

**Target Platform**: Linux-compatible API server and Docker Compose local
runtime.

**Project Type**: Backend web service.

**Performance Goals**: Analysis report input selection must be bounded and
documented for large asset sets; import must process larger sample-shaped
datasets with record-level partial success; paginated asset reads and graph
responses must remain bounded by existing API limits.

**Constraints**: Tenant isolation, no committed secrets, structured errors,
environment-driven configuration, reproducible local and Docker startup, analysis
rate limiting, grounded analysis with evidence IDs, graceful unavailable/failure
responses when provider configuration is missing or failing, and shared
certificate lifecycle logic using `metadata.expires` as source of truth.

**Scale/Scope**: Phase 7 only. Scope includes required analysis report endpoint,
certificate lifecycle classification and filters, sample-shaped import fields
`id`, `parent`, and `covers`, `parent` and `covers` relationship types, final
README and `.env.example` updates, and clean-start verification. Scope excludes
public registration, public organization creation, organization switching, live
asset scanning, cross-organization reports, and multi-organization membership.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Tenant isolation**: PASS. Analysis, certificate filters, import relationship
  resolution, and graph output derive `organization_id` only from the
  authenticated user. Import-local IDs and relationship references are resolved
  only inside the current authenticated import context.
- **Security defaults**: PASS. Analysis secrets are environment-driven and
  documented with safe placeholders. Missing or failing providers return
  structured unavailable/failure responses without secrets or partial invented
  output. Existing RBAC boundaries remain in force for import, asset, and
  relationship operations.
- **Test coverage**: PASS. The plan identifies automated tests for analysis
  authentication, tenant isolation, filtering, no-match behavior, grounded
  evidence, provider unavailable/failure behavior, certificate lifecycle states,
  import relationship references, graph lifecycle output, rate limits, and final
  documentation.
- **Lifecycle integrity**: PASS. Import changes preserve deduplication,
  `first_seen`, `last_seen`, tag and metadata merge behavior, stale reactivation,
  raw `metadata.expires`, malformed expiry reporting, and partial success for
  imperfect records.
- **Operational reproducibility**: PASS. `.env.example`, README, Docker Compose
  notes if needed, seed instructions, lint/test commands, and final verification
  steps are in scope. Analysis provider absence degrades gracefully for core
  workflows.
- **Code documentation**: PASS. New or modified Python functions, class methods,
  service methods, provider methods, and repository methods must include concise
  docstrings.

## Project Structure

### Documentation (this feature)

```text
specs/007-analysis-submission-polish/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- analysis-report-api.md
|   |-- asset-lifecycle-api.md
|   `-- import-sample-api.md
`-- tasks.md
```

### Source Code (repository root)

```text
app/
|-- api/
|   |-- deps.py
|   `-- routes/
|       |-- analysis.py
|       `-- assets.py
|-- core/
|   |-- config.py
|   `-- errors.py
|-- models/
|   `-- asset.py
|-- repositories/
|   |-- assets.py
|   `-- relationships.py
|-- schemas/
|   |-- analysis.py
|   `-- assets.py
|-- services/
|   |-- analysis.py
|   |-- certificate_lifecycle.py
|   |-- rate_limits.py
|   `-- tenant_assets.py
`-- main.py

tests/
|-- contract/
|   `-- test_analysis_api.py
|-- integration/
|   |-- test_analysis_report.py
|   |-- test_asset_certificate_lifecycle.py
|   |-- test_asset_import_sample_shape.py
|   `-- test_submission_documentation.py
`-- unit/
    |-- test_analysis_provider.py
    `-- test_certificate_lifecycle.py

alembic/
docker-compose.yml
Dockerfile
.env.example
README.md
```

**Structure Decision**: Use the existing backend layering. Add an analysis route,
schema, and service module instead of embedding provider logic in asset routes.
Add shared certificate lifecycle logic under `app/services/` so import, asset
serialization, filters, graph serialization, and analysis all call the same
classification rule. Extend existing asset import and relationship paths for
sample-shaped records rather than adding a parallel importer.

## Phase 0 Research Output

Research decisions are captured in [research.md](research.md). All planning
unknowns have been resolved; no `NEEDS CLARIFICATION` entries remain.

## Phase 1 Design Output

- Data model: [data-model.md](data-model.md)
- API contracts:
  - [contracts/analysis-report-api.md](contracts/analysis-report-api.md)
  - [contracts/asset-lifecycle-api.md](contracts/asset-lifecycle-api.md)
  - [contracts/import-sample-api.md](contracts/import-sample-api.md)
- Validation guide: [quickstart.md](quickstart.md)
- Agent context: `.github/copilot-instructions.md` points to this plan.

## Post-Design Constitution Check

- **Tenant isolation**: PASS. Contracts explicitly forbid client-supplied
  organization ownership and require evidence assets to belong to the current
  authenticated organization.
- **Security defaults**: PASS. Contracts define structured provider unavailable
  and failure responses, safe config placeholders, and no secret echoing.
- **Test coverage**: PASS. Quickstart and contracts define verification across
  analysis, lifecycle, import references, graph output, rate limits, and docs.
- **Lifecycle integrity**: PASS. Data model keeps `metadata.expires` as source
  of truth and treats lifecycle status as derived only.
- **Operational reproducibility**: PASS. Quickstart includes clean-start,
  migration, seed, test, lint, import, lifecycle, and analysis validation.
- **Code documentation**: PASS. Implementation tasks must include docstrings for
  all new or modified Python callables.

## Complexity Tracking

No constitution violations are planned.
