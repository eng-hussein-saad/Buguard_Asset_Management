# Feature Specification: Analysis Submission Polish

**Feature Branch**: `[007-analysis-submission-polish]`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 7 ONLY."

**Amendment**: User also requires this phase to ensure the bulk import capability can accept the provided illustrative asset import shape, including larger datasets, imperfect records, external record IDs, and relationship references such as parent and covers. The parent and covers references represent relationship types that must be supported even if they are not present in the current relationship type set.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Grounded Inventory Risk Reports (Priority: P1)

As an authenticated organization user, I need an optional natural-language inventory and risk report based only on my organization's real assets, so I can quickly understand asset exposure without risking invented or cross-tenant information.

**Why this priority**: The bonus analysis feature is valuable only if it is safe, tenant-scoped, and grounded in existing asset evidence. Any report that invents assets or uses another organization's data would violate the project's security model.

**Independent Test**: Authenticate as users from two organizations, request reports with asset filters, and verify each report summarizes only matching assets from the authenticated user's organization, includes risk details only for evidence-backed assets, and returns the asset IDs used as evidence.

**Acceptance Scenarios**:

1. **Given** an authenticated user has matching assets in their organization, **When** the user requests an inventory risk report with filters, **Then** the response includes a concise summary, risk entries tied to real assets, and the asset IDs used as evidence.
2. **Given** another organization has assets with overlapping values, **When** a user requests a report, **Then** the report includes no summary, risk, or evidence derived from the other organization's assets.
3. **Given** no assets match the requested filters, **When** the user requests a report, **Then** the response clearly states that no matching assets were available and returns no fabricated asset evidence.

---

### User Story 2 - Handle Analysis Configuration and Failures Safely (Priority: P1)

As an evaluator or maintainer, I need the optional analysis feature to fail gracefully when external analysis configuration is unavailable or an analysis service cannot produce a result, so the core asset management system remains usable and understandable.

**Why this priority**: Phase 7 allows the analysis feature only if time allows. Optional services must not make the base submission fragile or prevent evaluators from running the project.

**Independent Test**: Run the project without optional analysis configuration and with a simulated analysis failure, then verify normal asset workflows still work and analysis requests return clear structured failures without exposing secrets or internal details.

**Acceptance Scenarios**:

1. **Given** optional analysis configuration is missing, **When** an authenticated user requests a report, **Then** the request fails with a clear structured message explaining that analysis is unavailable.
2. **Given** the analysis provider cannot complete a report, **When** an authenticated user requests a report, **Then** the system returns a clear structured failure and does not return partial, invented, or cross-tenant data.
3. **Given** normal asset workflows are used while analysis is unavailable, **When** users list, import, update, or relate assets, **Then** those workflows continue to behave normally.

---

### User Story 3 - Finalize Submission Documentation (Priority: P1)

As an evaluator, I need complete setup, usage, design, and verification documentation, so I can run the project from a clean checkout, log in with seeded users, understand the architecture, and verify the implemented features without reverse-engineering the code.

**Why this priority**: Final submission quality depends on reproducibility and clarity. The evaluator must be able to boot, seed, authenticate, inspect, test, and understand the project from documented steps.

**Independent Test**: Start from a clean checkout, follow the README and example environment file, seed users, log in, exercise documented workflows, and run the documented verification commands successfully.

**Acceptance Scenarios**:

1. **Given** an evaluator has a clean checkout, **When** they follow the documented setup and container instructions, **Then** the project starts successfully with required services.
2. **Given** an evaluator follows the seed instructions, **When** they use the documented seeded credentials, **Then** they can authenticate and exercise role-appropriate workflows.
3. **Given** an evaluator reads the final documentation, **When** they review project behavior, **Then** they can understand multi-tenancy, role permissions, deduplication, relationships, graph usage if present, optional analysis behavior if implemented, known tradeoffs, and future improvements.

---

### User Story 4 - Import Relationship-Rich Sample Datasets (Priority: P1)

As an evaluator, I need the bulk import capability to accept the provided dataset shape with domains, subdomains, certificates, tags, metadata, and record-to-record references, so I can load realistic asset inventory data without manually transforming the dataset first.

**Why this priority**: Final submission must work with the assessment dataset, which may be larger than the sample and may contain imperfect records. The import path must preserve valid inventory data, report bad records clearly, and create supported relationships from import references.

**Independent Test**: Import a dataset using records shaped like the sample, including a domain with id a1, a subdomain with parent a1, and a certificate with covers a2, then verify valid assets are imported, parent and covers relationship types are supported, those relationships are created within the authenticated organization, malformed records are reported, and the overall import does not fail solely because some records are imperfect.

**Acceptance Scenarios**:

1. **Given** a dataset contains domain, subdomain, and certificate records with id, type, value, status, source, tags, metadata, parent, and covers fields, **When** an authorized user imports it, **Then** the valid assets are created or refreshed in the authenticated organization.
2. **Given** a subdomain record references a domain record through parent, **When** both records are valid and available in the same import, **Then** the system records a parent relationship from the subdomain to its parent domain within the authenticated organization.
3. **Given** a certificate record references a subdomain record through covers, **When** both records are valid and available in the same import, **Then** the system records a covers relationship from the certificate to the covered subdomain within the authenticated organization.
4. **Given** a larger dataset contains imperfect records, **When** an authorized user imports it, **Then** valid records are still processed and invalid records are reported with enough detail for the evaluator to understand what was skipped.

---

### User Story 5 - Verify Final Submission Readiness (Priority: P2)

As a maintainer, I need a final readiness checklist covering clean startup, tests, linting, examples, and known tradeoffs, so the submitted repository reflects the completed project state.

**Why this priority**: Final polish catches omissions that are easy to miss after feature work, especially outdated environment variables, missing examples, stale setup steps, or undocumented limitations.

**Independent Test**: Follow the final verification steps from a clean state and confirm every documented command, credential, workflow example, and tradeoff note matches the current project behavior.

**Acceptance Scenarios**:

1. **Given** all phase work is complete, **When** final verification runs from a clean state, **Then** startup, tests, linting, and documented examples complete as described.
2. **Given** a required environment variable or setup step exists, **When** the evaluator reviews the example environment and README, **Then** the required item is documented with safe placeholder values.
3. **Given** a known limitation remains, **When** the evaluator reviews the README, **Then** the limitation is clearly stated as a tradeoff or future improvement.

### Edge Cases

- Analysis requests must require authentication before any organization-owned data is selected.
- Analysis inputs must be scoped to the authenticated user's organization and must not accept organization ownership from request input.
- Analysis filters must not allow a user to infer whether another organization has matching assets.
- Reports must not invent asset IDs, asset values, risks, counts, or relationships that are not present in the selected organization-owned assets.
- Reports must include evidence asset IDs for every risk entry that refers to a specific asset.
- Empty matching asset sets must produce an explicit no-data result rather than fabricated analysis.
- Large matching asset sets must be summarized within documented limits while preserving evidence traceability.
- Optional analysis configuration must be documented without committing secrets.
- Optional analysis failures must not break authentication, asset management, imports, relationships, graph reads, tests, or documentation workflows.
- Bulk imports must accept records with external import IDs used for resolving relationships inside the submitted dataset.
- Bulk imports must accept the sample fields id, type, value, status, source, tags, metadata, parent, and covers where relevant to the asset type.
- Bulk imports must support a parent relationship type from a subdomain to its parent domain, even if that relationship type does not exist before this phase.
- Bulk imports must support a covers relationship type from a certificate to the subdomain it covers, even if that relationship type does not exist before this phase.
- Bulk imports must handle larger datasets than the illustrative sample without changing the accepted record shape.
- Bulk imports must report imperfect records without discarding unrelated valid records from the same dataset.
- Bulk import relationship references must be resolved only within the authenticated organization's import context.
- Bulk import relationship references to missing, invalid, skipped, duplicate, or cross-organization records must be reported clearly without creating unsafe relationships.
- Bulk import metadata must preserve nested values such as issuer and expiry information when supplied for certificates.
- Documentation must clearly state that public user registration and public organization creation are out of scope.
- Documentation must clearly state that organizations and users are seeded for local development and evaluation.
- Documentation must clearly state that each user belongs to exactly one organization and has one role within that organization.
- Documentation must clearly state that organization ownership is derived from authenticated context, never client input.
- Documentation must clearly state that live scanning or asset discovery is out of scope and assets are imported from the provided dataset.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an optional authenticated inventory and risk report capability for organization users when analysis configuration is available.
- **FR-002**: Analysis reports MUST derive organization scope only from the authenticated user context.
- **FR-003**: Analysis report requests MUST support user-visible filters for selecting a subset of the authenticated organization's assets.
- **FR-004**: Analysis reports MUST use only existing assets that match the authenticated organization and requested filters.
- **FR-005**: Analysis reports MUST NOT invent assets, asset IDs, counts, relationships, ownership, statuses, or risk facts.
- **FR-006**: Analysis report responses MUST include a concise summary, a list of risks where applicable, and the asset IDs used as evidence.
- **FR-007**: Each risk entry that refers to a specific asset MUST include the asset ID that supports the risk.
- **FR-008**: When no assets match the requested filters, the report response MUST clearly state that no matching assets were available and return an empty evidence list.
- **FR-009**: Analysis failures caused by missing configuration or unavailable optional services MUST return clear structured messages without exposing secrets or internal details.
- **FR-010**: Missing or failing optional analysis services MUST NOT prevent core project startup, authentication, asset workflows, imports, relationship workflows, graph reads, or tests from running.
- **FR-011**: Analysis behavior MUST be covered by automated tests using controlled analysis output rather than relying on live external responses.
- **FR-012**: Analysis tests MUST verify authentication, tenant isolation, filtering, empty matches, grounded evidence, provider-unavailable behavior, and provider-failure behavior.
- **FR-013**: Analysis requests MUST be subject to the documented analysis rate limit policy from the reliability phase.
- **FR-014**: Bulk import MUST accept records shaped like the provided sample, including id, type, value, status, source, tags, metadata, parent, and covers fields where relevant.
- **FR-015**: Bulk import MUST treat each record id as an import-local external reference that can be used to resolve parent and covers relationships within the same authenticated organization import.
- **FR-016**: Bulk import MUST create or refresh valid domain, subdomain, and certificate assets from the sample-shaped dataset.
- **FR-017**: Bulk import MUST preserve supplied tags and metadata for valid imported assets, including certificate metadata such as issuer and expiry values.
- **FR-018**: System MUST support a parent relationship type representing a subdomain's parent domain.
- **FR-019**: System MUST support a covers relationship type representing a certificate covering a subdomain.
- **FR-020**: Bulk import MUST create a parent relationship when a valid subdomain record references a valid parent domain record.
- **FR-021**: Bulk import MUST create a covers relationship when a valid certificate record references a valid covered subdomain record.
- **FR-022**: Bulk import MUST NOT create relationships when the referenced record is missing, invalid, skipped, ambiguous, or outside the authenticated organization context.
- **FR-023**: Bulk import MUST process valid records from larger datasets even when unrelated records are imperfect.
- **FR-024**: Bulk import MUST report imperfect records and unresolved relationship references with enough detail for an evaluator to understand which records were skipped or partially processed.
- **FR-025**: Bulk import MUST NOT accept organization ownership from imported records or relationship references.
- **FR-026**: Bulk import behavior for the sample-shaped dataset MUST be covered by automated tests, including relationship type support, valid parent and covers references, larger batches, malformed records, unresolved references, and partial success reporting.
- **FR-027**: Project documentation MUST include a project overview, architecture summary, feature list, setup instructions, environment variables, container instructions, migration instructions, seed instructions, seeded user credentials, test instructions, request documentation location, authentication examples, and sample import example.
- **FR-028**: Project documentation MUST explain multi-tenancy, role-based permissions, deduplication strategy, relationship model behavior, graph visualization usage if implemented, optional analysis behavior if implemented, known tradeoffs, and future improvements.
- **FR-029**: Project documentation MUST state that public user registration and public organization creation are out of scope.
- **FR-030**: Project documentation MUST state that organizations and users are seeded for local development and evaluation.
- **FR-031**: Project documentation MUST state that each user belongs to exactly one organization and has one role within that organization.
- **FR-032**: Project documentation MUST state that multi-tenancy is enforced by scoping all assets and relationships to authenticated organization context.
- **FR-033**: Project documentation MUST state that organization ownership always comes from authenticated user context and never from client input.
- **FR-034**: Project documentation MUST state that supporting users across multiple organizations is a future enhancement.
- **FR-035**: Project documentation MUST state that live scanning and asset discovery are out of scope and assets are imported from the provided dataset.
- **FR-036**: The example environment file MUST list all required configuration values and any optional analysis configuration using safe placeholder values.
- **FR-037**: Final submission instructions MUST allow an evaluator to start from a clean state, run the project, seed data, authenticate with seeded users, run tests, and run linting.
- **FR-038**: Final submission examples MUST match the current implemented behavior for authentication, imports, asset workflows, relationships, graph usage if present, rate limits, and optional analysis if implemented.
- **FR-039**: Phase 7 MUST NOT add public registration, public organization creation, organization switching, live asset scanning, cross-organization reports, or unsupported multi-organization user membership.

### Key Entities

- **Analysis Report**: A generated inventory and risk summary for the authenticated organization, including summary text, risk entries, and the evidence asset IDs used to produce the report.
- **Analysis Filter**: User-visible selection criteria that narrow which organization-owned assets are eligible for a report.
- **Evidence Asset**: A real asset from the authenticated user's organization that matched the analysis request and supports the generated summary or a risk entry.
- **Risk Entry**: A report item describing a potential issue, its severity, reason, and supporting asset ID when tied to a specific asset.
- **Sample Import Record**: A dataset item representing an asset with an import-local id, asset type, value, status, source, tags, metadata, and optional relationship references.
- **Import Relationship Reference**: A field such as parent or covers that points to another record's import-local id and requests a relationship between imported assets.
- **Parent Relationship**: A relationship type connecting a subdomain to the domain that is its parent.
- **Covers Relationship**: A relationship type connecting a certificate to the subdomain that the certificate covers.
- **Imperfect Import Record**: A dataset item that is malformed, incomplete, unsupported, or references another record that cannot be safely resolved.
- **Seeded User Credential**: A documented local-development credential for a user assigned to exactly one organization and one role.
- **Final Submission Checklist**: The documented set of verification steps proving clean startup, seeded login, examples, tests, linting, and known tradeoffs are ready for evaluation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of analysis report responses for filtered requests include only evidence asset IDs belonging to the authenticated user's organization.
- **SC-002**: 100% of analysis tenant isolation tests confirm reports never include another organization's asset IDs, counts, risks, relationships, or asset values.
- **SC-003**: 100% of analysis no-match tests return an explicit no-data result with zero evidence asset IDs.
- **SC-004**: 100% of analysis failure tests return structured unavailable or failure messages without exposing secrets or disrupting core asset workflows.
- **SC-005**: 100% of analysis risks that refer to a specific asset include a valid evidence asset ID from the report input set.
- **SC-006**: 100% of sample-shaped valid domain, subdomain, and certificate records import successfully for an authorized user.
- **SC-007**: 100% of valid parent and covers references in the sample-shaped dataset create the expected parent and covers relationships inside the authenticated organization.
- **SC-008**: 100% of import tests with imperfect records confirm unrelated valid records are still processed and invalid records are reported.
- **SC-009**: 100% of unresolved, invalid, or unsafe import relationship references are reported without creating relationships.
- **SC-010**: 100% of final setup instructions can be followed from a clean checkout to start the project and authenticate with seeded users.
- **SC-011**: 100% of required environment variables and optional analysis configuration values are represented in the example environment file with safe placeholder values.
- **SC-012**: 100% of documented verification commands for tests and linting complete successfully before final submission, or any remaining failure is explicitly documented with its reason.
- **SC-013**: 100% of documented examples for authentication, imports, seeded credentials, and optional analysis if implemented match current project behavior.
- **SC-014**: An evaluator can read the README and identify all required scope assumptions, including no public registration, no public organization creation, single-organization users, authenticated organization scoping, no live scanning, and future multi-organization support.

## Assumptions

- Phase 1 has already established the backend foundation, local and container startup paths, migration workflow, and baseline documentation.
- Phase 2 has already established organizations, seeded users, authentication, refresh tokens, authenticated organization context, and role-based permissions.
- Phase 3 has already established tenant-scoped asset creation, reading, updating, filtering, sorting, pagination, validation, and structured errors.
- Phase 4 has already established bulk import from the provided dataset, idempotent observation behavior, lifecycle handling, and import summaries.
- Phase 5 has already established relationship management, relationship listing, graph retrieval, and graph visualization usage if implemented.
- Phase 6 has already established comprehensive tests, continuous quality checks, rate limiting, organization-scoped caching, and related documentation.
- Phase 7 is limited to the optional grounded analysis report, sample-shaped bulk import compatibility, final README, example environment updates, clean-start verification instructions, and final submission polish.
- The analysis feature is optional for final submission, but if implemented it must satisfy all tenant isolation, grounding, documentation, graceful failure, and test requirements in this specification.
- The supplied import sample is illustrative; the real assessment dataset may be larger and may include imperfect records that require partial success reporting.
