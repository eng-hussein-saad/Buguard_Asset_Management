# Feature Specification: Analysis Submission Polish

**Feature Branch**: `[007-analysis-submission-polish]`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Read PLAN.md and create a specification for phase 7 ONLY."

**Amendment**: User also requires this phase to ensure the bulk import capability can accept the provided illustrative asset import shape, including larger datasets, imperfect records, external record IDs, and relationship references such as parent and covers. The parent and covers references represent relationship types that must be supported even if they are not present in the current relationship type set.

**Amendment**: User clarified that the analysis report is required, not optional, and must include certificate lifecycle date handling that distinguishes expired certificates from certificates expiring soon.

**Amendment**: Certificate lifecycle handling must be shared across import, asset views, filtering, graph display, documentation, examples, tests, and analysis. Certificate `metadata.expires` remains the source of truth, while derived lifecycle status is computed from that value.

## Clarifications

### Session 2026-06-28

- Q: Which availability behavior should Phase 7 require for `/analysis/report`? -> A: Required endpoint with configured analysis provider; missing/unavailable provider returns structured unavailable response.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Grounded Inventory Risk Reports (Priority: P1)

As an authenticated organization user, I need a natural-language inventory and risk report based only on my organization's real assets, so I can quickly understand asset exposure without risking invented or cross-tenant information.

**Why this priority**: The analysis feature is required for this phase and is valuable only if it is safe, tenant-scoped, and grounded in existing asset evidence. Any report that invents assets or uses another organization's data would violate the project's security model.

**Independent Test**: Authenticate as users from two organizations, request reports with asset filters, and verify each report summarizes only matching assets from the authenticated user's organization, includes risk details only for evidence-backed assets, identifies expired and expiring-soon certificates from lifecycle dates, and returns the asset IDs used as evidence.

**Acceptance Scenarios**:

1. **Given** an authenticated user has matching assets in their organization, **When** the user requests an inventory risk report with filters, **Then** the response includes a concise summary, risk entries tied to real assets, and the asset IDs used as evidence.
2. **Given** another organization has assets with overlapping values, **When** a user requests a report, **Then** the report includes no summary, risk, or evidence derived from the other organization's assets.
3. **Given** no assets match the requested filters, **When** the user requests a report, **Then** the response clearly states that no matching assets were available and returns no fabricated asset evidence.
4. **Given** matching certificate assets include lifecycle expiry dates, **When** the user requests an inventory risk report, **Then** the response distinguishes certificates that are already expired from certificates expiring soon and ties each finding to evidence asset IDs.

---

### User Story 2 - Handle Required Analysis Configuration and Failures Safely (Priority: P1)

As an evaluator or maintainer, I need required analysis setup to be documented and analysis failures to be handled gracefully, so the core asset management system remains usable and any report failure is understandable.

**Why this priority**: Phase 7 requires the analysis feature, but external analysis failures must not make the base asset management workflows fragile or expose sensitive details.

**Independent Test**: Run the project with required analysis configuration documented and with a simulated analysis failure, then verify normal asset workflows still work and analysis requests return clear structured failures without exposing secrets or internal details.

**Acceptance Scenarios**:

1. **Given** required analysis configuration is missing, **When** an evaluator follows setup or verification instructions, **Then** the missing configuration is clearly identifiable from documented setup requirements and authenticated analysis requests return a structured unavailable response.
2. **Given** the configured analysis provider cannot complete a report, **When** an authenticated user requests a report, **Then** the system returns a clear structured unavailable or failure response and does not return partial, invented, or cross-tenant data.
3. **Given** normal asset workflows are used while analysis is unavailable, **When** users list, import, update, or relate assets, **Then** those workflows continue to behave normally.

---

### User Story 3 - Finalize Submission Documentation (Priority: P1)

As an evaluator, I need complete setup, usage, design, and verification documentation, so I can run the project from a clean checkout, log in with seeded users, understand the architecture, and verify the implemented features without reverse-engineering the code.

**Why this priority**: Final submission quality depends on reproducibility and clarity. The evaluator must be able to boot, seed, authenticate, inspect, test, and understand the project from documented steps.

**Independent Test**: Start from a clean checkout, follow the README and example environment file, seed users, log in, exercise documented workflows, and run the documented verification commands successfully.

**Acceptance Scenarios**:

1. **Given** an evaluator has a clean checkout, **When** they follow the documented setup and container instructions, **Then** the project starts successfully with required services.
2. **Given** an evaluator follows the seed instructions, **When** they use the documented seeded credentials, **Then** they can authenticate and exercise role-appropriate workflows.
3. **Given** an evaluator reads the final documentation, **When** they review project behavior, **Then** they can understand multi-tenancy, role permissions, deduplication, relationships, graph usage if present, required analysis behavior, certificate lifecycle handling, known tradeoffs, and future improvements.

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

---

### User Story 6 - Review Certificate Lifecycle Outside Analysis (Priority: P2)

As an evaluator, I need certificate lifecycle status to appear in imported results, asset views, filters, and graph context, so I can inspect expired and expiring-soon certificates without relying only on the analysis report.

**Why this priority**: Certificate lifecycle risk should be a shared asset capability. Keeping `metadata.expires` as the source of truth and deriving lifecycle status consistently prevents analysis from having a separate private interpretation.

**Independent Test**: Import certificate assets with expired, expiring-soon, valid future, missing, and malformed `metadata.expires` values, then verify import reporting, asset read responses, asset list responses, lifecycle filters, graph nodes, documentation, and analysis use the same lifecycle classification.

**Acceptance Scenarios**:

1. **Given** a certificate import record contains a valid `metadata.expires` date, **When** the record is imported, **Then** the raw expiry remains in metadata and the lifecycle status can be derived consistently.
2. **Given** a certificate import record contains malformed `metadata.expires`, **When** the record is imported, **Then** the import reports the malformed lifecycle value while preserving the record according to normal import rules.
3. **Given** users read or list certificate assets, **When** certificate lifecycle data is available, **Then** each certificate response includes a derived lifecycle status based on `metadata.expires`.
4. **Given** users filter certificate assets by lifecycle status, **When** they request expired or expiring-soon certificates, **Then** results include only matching certificates from the authenticated organization.
5. **Given** users view an asset graph containing certificates, **When** graph data is returned, **Then** certificate nodes expose lifecycle status, especially for certificates connected to subdomains through covers relationships.

### Edge Cases

- Analysis requests must require authentication before any organization-owned data is selected.
- Analysis inputs must be scoped to the authenticated user's organization and must not accept organization ownership from request input.
- Analysis filters must not allow a user to infer whether another organization has matching assets.
- Reports must not invent asset IDs, asset values, risks, counts, or relationships that are not present in the selected organization-owned assets.
- Reports must include evidence asset IDs for every risk entry that refers to a specific asset.
- Empty matching asset sets must produce an explicit no-data result rather than fabricated analysis.
- Large matching asset sets must be summarized within documented limits while preserving evidence traceability.
- Analysis configuration must be documented without committing secrets.
- Analysis failures must not break authentication, asset management, imports, relationships, graph reads, tests, or documentation workflows.
- Analysis must identify expired certificates based on certificate lifecycle expiry dates earlier than the evaluation date.
- Analysis must identify expiring-soon certificates based on certificate lifecycle expiry dates from the evaluation date through the next 30 calendar days.
- Analysis must handle missing, malformed, or unparseable certificate lifecycle dates without inventing expiry status.
- Analysis must include certificate lifecycle risk evidence using the relevant certificate asset IDs.
- Certificate metadata.expires must remain the source of truth for certificate lifecycle dates.
- Certificate lifecycle status must be derived consistently as expired, expiring_soon, valid, or unknown.
- Certificate lifecycle classification must be shared by import reporting, asset read responses, asset list responses, lifecycle filters, graph responses, and analysis.
- Certificate lifecycle filters must never include certificates from another organization.
- Malformed certificate metadata.expires values must be visible to evaluators without discarding unrelated valid import records.
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

- **FR-001**: System MUST provide an authenticated inventory and risk report capability for organization users.
- **FR-002**: Analysis reports MUST derive organization scope only from the authenticated user context.
- **FR-003**: Analysis report requests MUST support user-visible filters for selecting a subset of the authenticated organization's assets.
- **FR-004**: Analysis reports MUST use only existing assets that match the authenticated organization and requested filters.
- **FR-005**: Analysis reports MUST NOT invent assets, asset IDs, counts, relationships, ownership, statuses, or risk facts.
- **FR-006**: Analysis report responses MUST include a concise summary, a list of risks where applicable, and the asset IDs used as evidence.
- **FR-007**: Each risk entry that refers to a specific asset MUST include the asset ID that supports the risk.
- **FR-008**: When no assets match the requested filters, the report response MUST clearly state that no matching assets were available and return an empty evidence list.
- **FR-009**: Analysis configuration required for successful report generation MUST be documented with safe placeholder values.
- **FR-010**: The analysis report endpoint MUST exist for Phase 7, and missing, unavailable, or failing analysis provider configuration MUST return a clear structured unavailable or failure response without exposing secrets, internal details, partial reports, invented data, or cross-tenant report data.
- **FR-011**: Missing or failing analysis services MUST NOT prevent core project startup, authentication, asset workflows, imports, relationship workflows, graph reads, or tests from running.
- **FR-012**: Analysis reports MUST evaluate certificate lifecycle expiry dates for certificate assets included in the report input set.
- **FR-013**: Analysis reports MUST classify certificates with expiry dates earlier than the evaluation date as expired.
- **FR-014**: Analysis reports MUST classify certificates with expiry dates from the evaluation date through the next 30 calendar days as expiring soon.
- **FR-015**: Analysis reports MUST NOT classify certificates with missing, malformed, or unparseable expiry dates as expired or expiring soon.
- **FR-016**: Certificate lifecycle findings MUST include the relevant certificate asset IDs as evidence.
- **FR-017**: Analysis behavior MUST be covered by automated tests using controlled analysis output rather than relying on live external responses.
- **FR-018**: Analysis tests MUST verify authentication, tenant isolation, filtering, empty matches, grounded evidence, unavailable analysis behavior, analysis failure behavior, expired certificates, expiring-soon certificates, future-valid certificates, and malformed certificate dates.
- **FR-019**: Analysis requests MUST be subject to the documented analysis rate limit policy from the reliability phase.
- **FR-020**: Certificate metadata.expires MUST remain the source of truth for certificate lifecycle dates.
- **FR-021**: System MUST provide a shared certificate lifecycle classification rule that derives lifecycle status from metadata.expires.
- **FR-022**: Shared certificate lifecycle status MUST use expired, expiring_soon, valid, or unknown values.
- **FR-023**: Certificate assets with expiry dates earlier than the evaluation date MUST have derived lifecycle status expired.
- **FR-024**: Certificate assets with expiry dates from the evaluation date through the next 30 calendar days MUST have derived lifecycle status expiring_soon.
- **FR-025**: Certificate assets with valid expiry dates after the expiring-soon window MUST have derived lifecycle status valid.
- **FR-026**: Certificate assets with missing, malformed, or unparseable metadata.expires values MUST have derived lifecycle status unknown.
- **FR-027**: Bulk import MUST validate certificate metadata.expires when present, preserve the raw value in metadata, and report malformed expiry values so lifecycle data quality is visible.
- **FR-028**: Asset read responses for certificate assets MUST include derived lifecycle status without moving or duplicating the raw metadata.expires source of truth.
- **FR-029**: Asset list responses for certificate assets MUST include derived lifecycle status without moving or duplicating the raw metadata.expires source of truth.
- **FR-030**: Asset listing MUST support evaluator-friendly certificate lifecycle filters for expired and expiring_soon certificates within the authenticated organization.
- **FR-031**: Certificate lifecycle filters MUST NOT return, count, or imply certificate assets outside the authenticated organization.
- **FR-032**: Asset graph responses MUST expose certificate lifecycle status for certificate nodes, including certificate nodes connected to subdomains through covers relationships.
- **FR-033**: Analysis reports MUST use the shared certificate lifecycle classification rule rather than a separate analysis-only interpretation.
- **FR-034**: Bulk import MUST accept records shaped like the provided sample, including id, type, value, status, source, tags, metadata, parent, and covers fields where relevant.
- **FR-035**: Bulk import MUST treat each record id as an import-local external reference that can be used to resolve parent and covers relationships within the same authenticated organization import.
- **FR-036**: Bulk import MUST create or refresh valid domain, subdomain, and certificate assets from the sample-shaped dataset.
- **FR-037**: Bulk import MUST preserve supplied tags and metadata for valid imported assets, including certificate metadata such as issuer and expiry values.
- **FR-038**: System MUST support a parent relationship type representing a subdomain's parent domain.
- **FR-039**: System MUST support a covers relationship type representing a certificate covering a subdomain.
- **FR-040**: Bulk import MUST create a parent relationship when a valid subdomain record references a valid parent domain record.
- **FR-041**: Bulk import MUST create a covers relationship when a valid certificate record references a valid covered subdomain record.
- **FR-042**: Bulk import MUST NOT create relationships when the referenced record is missing, invalid, skipped, ambiguous, or outside the authenticated organization context.
- **FR-043**: Bulk import MUST process valid records from larger datasets even when unrelated records are imperfect.
- **FR-044**: Bulk import MUST report imperfect records and unresolved relationship references with enough detail for an evaluator to understand which records were skipped or partially processed.
- **FR-045**: Bulk import MUST NOT accept organization ownership from imported records or relationship references.
- **FR-046**: Bulk import behavior for the sample-shaped dataset MUST be covered by automated tests, including relationship type support, valid parent and covers references, larger batches, malformed records, unresolved references, partial success reporting, and malformed certificate expiry reporting.
- **FR-047**: Automated tests MUST cover shared certificate lifecycle classification for expired, expiring_soon, valid, unknown missing expiry, and unknown malformed expiry cases.
- **FR-048**: Automated tests MUST cover certificate lifecycle status in import reporting, asset read responses, asset list responses, lifecycle filters, graph responses, and analysis reports.
- **FR-049**: Project documentation MUST include a project overview, architecture summary, feature list, setup instructions, environment variables, container instructions, migration instructions, seed instructions, seeded user credentials, test instructions, request documentation location, authentication examples, and sample import example.
- **FR-050**: Project documentation MUST explain multi-tenancy, role-based permissions, deduplication strategy, relationship model behavior, graph visualization usage if implemented, required analysis behavior, certificate lifecycle handling, known tradeoffs, and future improvements.
- **FR-051**: Project documentation MUST state that certificate lifecycle status is derived from certificate metadata.expires and that metadata.expires remains the source of truth.
- **FR-052**: Project documentation MUST include examples for expired, expiring-soon, valid future, missing expiry, and malformed expiry certificate records.
- **FR-053**: Project documentation MUST state that public user registration and public organization creation are out of scope.
- **FR-054**: Project documentation MUST state that organizations and users are seeded for local development and evaluation.
- **FR-055**: Project documentation MUST state that each user belongs to exactly one organization and has one role within that organization.
- **FR-056**: Project documentation MUST state that multi-tenancy is enforced by scoping all assets and relationships to authenticated organization context.
- **FR-057**: Project documentation MUST state that organization ownership always comes from authenticated user context and never from client input.
- **FR-058**: Project documentation MUST state that supporting users across multiple organizations is a future enhancement.
- **FR-059**: Project documentation MUST state that live scanning and asset discovery are out of scope and assets are imported from the provided dataset.
- **FR-060**: The example environment file MUST list all required configuration values and analysis configuration using safe placeholder values.
- **FR-061**: Final submission instructions MUST allow an evaluator to start from a clean state, run the project, seed data, authenticate with seeded users, run tests, and run linting.
- **FR-062**: Final submission examples MUST match the current implemented behavior for authentication, imports, seeded credentials, asset workflows, certificate lifecycle filters, relationships, graph usage if present, rate limits, and analysis.
- **FR-063**: Phase 7 MUST NOT add public registration, public organization creation, organization switching, live asset scanning, cross-organization reports, or unsupported multi-organization user membership.

### Key Entities

- **Analysis Report**: A generated inventory and risk summary for the authenticated organization, including summary text, risk entries, and the evidence asset IDs used to produce the report.
- **Analysis Filter**: User-visible selection criteria that narrow which organization-owned assets are eligible for a report.
- **Evidence Asset**: A real asset from the authenticated user's organization that matched the analysis request and supports the generated summary or a risk entry.
- **Risk Entry**: A report item describing a potential issue, its severity, reason, and supporting asset ID when tied to a specific asset.
- **Certificate Lifecycle Date**: A certificate expiry date used to classify certificate risk as expired, expiring soon, or not currently expiring.
- **Certificate Lifecycle Status**: A derived value computed from certificate metadata.expires, using expired, expiring_soon, valid, or unknown.
- **Certificate Lifecycle Filter**: A user-visible filter that narrows certificate assets by derived lifecycle status within the authenticated organization.
- **Expired Certificate Finding**: A risk entry for a certificate whose expiry date is earlier than the evaluation date.
- **Expiring-Soon Certificate Finding**: A risk entry for a certificate whose expiry date is from the evaluation date through the next 30 calendar days.
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
- **SC-006**: 100% of expired certificate test cases are reported as expired and include the relevant certificate asset IDs.
- **SC-007**: 100% of certificate test cases expiring within 30 calendar days are reported as expiring soon and include the relevant certificate asset IDs.
- **SC-008**: 100% of certificate test cases expiring after the 30-day window are not reported as expired or expiring soon.
- **SC-009**: 100% of certificate lifecycle classification tests produce the same status for import reporting, asset read responses, asset list responses, lifecycle filters, graph responses, and analysis reports.
- **SC-010**: 100% of malformed certificate metadata.expires import tests report the malformed expiry value while preserving unrelated valid records.
- **SC-011**: 100% of certificate lifecycle filter tests return only matching certificates from the authenticated organization.
- **SC-012**: 100% of certificate graph response tests expose lifecycle status for certificate nodes.
- **SC-013**: 100% of sample-shaped valid domain, subdomain, and certificate records import successfully for an authorized user.
- **SC-014**: 100% of valid parent and covers references in the sample-shaped dataset create the expected parent and covers relationships inside the authenticated organization.
- **SC-015**: 100% of import tests with imperfect records confirm unrelated valid records are still processed and invalid records are reported.
- **SC-016**: 100% of unresolved, invalid, or unsafe import relationship references are reported without creating relationships.
- **SC-017**: 100% of final setup instructions can be followed from a clean checkout to start the project and authenticate with seeded users.
- **SC-018**: 100% of required environment variables and analysis configuration values are represented in the example environment file with safe placeholder values.
- **SC-019**: 100% of documented verification commands for tests and linting complete successfully before final submission, or any remaining failure is explicitly documented with its reason.
- **SC-020**: 100% of documented examples for authentication, imports, seeded credentials, certificate lifecycle, and analysis match current project behavior.
- **SC-021**: An evaluator can read the README and identify all required scope assumptions, including no public registration, no public organization creation, single-organization users, authenticated organization scoping, no live scanning, and future multi-organization support.

## Assumptions

- Phase 1 has already established the backend foundation, local and container startup paths, migration workflow, and baseline documentation.
- Phase 2 has already established organizations, seeded users, authentication, refresh tokens, authenticated organization context, and role-based permissions.
- Phase 3 has already established tenant-scoped asset creation, reading, updating, filtering, sorting, pagination, validation, and structured errors.
- Phase 4 has already established bulk import from the provided dataset, idempotent observation behavior, lifecycle handling, and import summaries.
- Phase 5 has already established relationship management, relationship listing, graph retrieval, and graph visualization usage if implemented.
- Phase 6 has already established comprehensive tests, continuous quality checks, rate limiting, organization-scoped caching, and related documentation.
- Phase 7 is limited to the required grounded analysis report, certificate lifecycle risk handling, sample-shaped bulk import compatibility, final README, example environment updates, clean-start verification instructions, and final submission polish.
- The analysis report endpoint is required for final submission; successful report generation depends on documented analysis provider configuration, and missing or unavailable providers return structured unavailable responses.
- Certificate metadata.expires remains the source of truth for certificate lifecycle dates; lifecycle_status is derived for convenience and consistency.
- Expiring soon means a certificate expiry date from the evaluation date through the next 30 calendar days.
- The supplied import sample is illustrative; the real assessment dataset may be larger and may include imperfect records that require partial success reporting.
