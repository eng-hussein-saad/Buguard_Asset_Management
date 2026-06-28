# Phase 0 Research: Analysis Submission Polish

## Decision: Provide a required `/analysis/report` endpoint with graceful provider unavailability

**Rationale**: The feature requires the analysis report endpoint for final
submission, but missing or failing provider configuration must not break core
asset workflows. A required route with structured unavailable/failure responses
keeps the API contract visible while preserving reproducible local startup.

**Alternatives considered**: Making analysis optional was rejected because the
spec clarifies the report is required. Failing application startup when provider
configuration is missing was rejected because operational reproducibility and
core asset workflows must keep working.

## Decision: Use an environment-driven analysis provider abstraction and fake provider in tests

**Rationale**: The service can gather tenant-scoped evidence, build a constrained
prompt/input package, call a provider adapter, and validate the returned report
against the evidence set. Tests can inject a deterministic fake provider and
exercise failure cases without live external network calls.

**Alternatives considered**: Calling a live provider in tests was rejected as
non-reproducible. Handwritten report generation only was rejected because the
phase requires analysis-provider configuration and unavailable behavior.

## Decision: Validate provider output against selected evidence before returning it

**Rationale**: Reports must not invent asset IDs, counts, risks, relationships,
or asset values. The analysis service should treat selected organization-owned
assets as the evidence boundary and reject or sanitize provider output that
references assets outside that boundary.

**Alternatives considered**: Trusting provider output directly was rejected
because it risks hallucinated or cross-tenant evidence. Persisting every report
was deferred because the spec does not require report history.

## Decision: Centralize certificate lifecycle classification in a shared service

**Rationale**: Import reporting, asset read/list responses, lifecycle filters,
graph nodes, documentation examples, tests, and analysis must classify
certificates consistently. A shared classifier keeps `metadata.expires` as the
source of truth and derives only `expired`, `expiring_soon`, `valid`, or
`unknown` at response/query time.

**Alternatives considered**: Storing lifecycle status as a separate mutable
field was rejected because it duplicates `metadata.expires` and can drift.
Embedding classification independently in analysis was rejected because the
spec requires shared behavior across surfaces.

## Decision: Use evaluation date plus a 30-calendar-day inclusive window for expiring soon

**Rationale**: The spec defines expired as dates earlier than the evaluation date
and expiring soon as dates from the evaluation date through the next 30 calendar
days. The classifier should accept an evaluation date so tests are deterministic.

**Alternatives considered**: Using wall-clock time directly inside every caller
was rejected because tests and analysis evidence need deterministic dates.

## Decision: Extend the existing import path for sample-shaped records

**Rationale**: Existing import already owns tenant-scoped observation lifecycle,
deduplication, tag/metadata merge, status refresh, partial success, and
structured errors. Extending the validator to accept import-local `id`, `parent`,
and `covers` fields preserves established behavior and avoids a parallel import
pipeline.

**Alternatives considered**: Adding a new sample-only endpoint was rejected
because evaluators should not have to choose between import modes. Rejecting
unknown relationship fields was rejected because the final dataset may include
the provided relationship references.

## Decision: Resolve import relationship references after valid asset observations

**Rationale**: Relationship references such as `parent` and `covers` depend on
successful import-local ID resolution. Processing valid asset records first,
then creating relationships only for valid same-import references, supports
partial success while preventing relationships to missing, invalid, skipped,
ambiguous, or cross-organization records.

**Alternatives considered**: Creating relationships as records stream in was
rejected because referenced assets may appear later in the same dataset. Creating
placeholder assets for missing references was rejected because it invents
inventory data.

## Decision: Add `parent` and `covers` relationship types to the shared relationship model

**Rationale**: The spec requires these relationship types even if they are not
present today. They should be available to both import-created relationships and
normal relationship/graph serialization so graph behavior remains consistent.

**Alternatives considered**: Representing relationship type only inside metadata
was rejected because it would bypass existing relationship filtering, duplicate
checks, and graph labels.

## Decision: Update final documentation as a first-class deliverable

**Rationale**: Final submission readiness depends on evaluators being able to
start clean, seed users, authenticate, import sample data, inspect lifecycle
status, exercise graph and analysis behavior, run tests/linting, and understand
scope limits without reading code.

**Alternatives considered**: Relying on tests as documentation was rejected
because the spec explicitly requires README, environment, examples, scope
assumptions, known tradeoffs, and final verification instructions.
