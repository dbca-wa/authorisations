# Schema Migration Plan

## Objective

Design and deliver a reusable, safe migration framework for both Questionnaire.document and Application.document so schema changes can be applied to all existing records in a controlled maintenance window, with deterministic rollback.

The framework prioritises:
- data safety
- operational clarity
- strict runtime behaviour
- low implementation complexity
- repeatability for future migrations

## Confirmed Decisions

The following decisions are fixed for this plan:
- Backup model: same-table backup columns on Questionnaire and Application.
- Migration execution: maintenance window plus single transaction migration run.
- Write policy during migration: block document writes.
- Runtime policy after migration: strict current-version-only acceptance.
- First implementation target: migration framework first, no broad schema-shape change.
- First experiment: version-only migration to validate end-to-end mechanics.
- Backup retention: keep backup copies until manually approved for cleanup.

## Scope

### In Scope
- Version-aware schema resolution for Questionnaire and Application documents.
- Reusable migration registries and transformation pipeline.
- Backup capture and rollback support on both models.
- Management command modes: report, dry-run, migrate, rollback, clear-backup.
- Validation guarantees before and after transformation.
- Test and fixture updates for migration paths.
- Operational runbook integration for deployment and rollback.

### Out of Scope for Initial Delivery
- Long-lived dual-version runtime support.
- Automatic periodic cleanup of backup copies.
- Broad questionnaire/application schema shape redesign.
- Key-contract redesign for answer keys and attachment question keys.

## Safety Invariants

These must hold throughout all migrations:
- Questionnaire document remains structurally valid against its target schema.
- Application document remains structurally valid against its target schema.
- Existing key contracts remain unchanged in framework phase:
  - Application answers use section-question keys.
  - Attachment.question uses step.section-question keys.
- Runtime API validation remains strict and does not accept obsolete versions after cutover.
- Rollback must restore original document payload and original schema version.

## Architecture

### 1. Versioned Schema Resolution

Introduce schema resolution that supports:
- get current schema for runtime validation
- get explicit schema for migration source and target validation

Target files:
- backend/questionnaires/schema.py
- backend/applications/schema.py

### 2. Migration Registries

Define ordered migration registries for each document type:
- explicit version-to-version transforms
- deterministic path resolution
- hard failure for unknown or partial paths

Target placement:
- backend/questionnaires (new migration support module)
- backend/applications (new migration support module)

### 3. Backup Strategy (Same Table)

Add backup metadata fields on both models:
- backup_document (JSON copy before transform)
- backup_schema_version
- backup_created_at
- migration_run_id

Target files:
- backend/questionnaires/models.py
- backend/applications/models.py

### 4. Operational Command Interface

Add one management command with explicit modes:
- report: show current version distribution and readiness checks
- dry-run: execute transform plus validate pipeline without writes
- migrate: backup then transform and validate in one transaction
- rollback: restore by migration_run_id
- clear-backup: explicit cleanup only

Safety guards:
- require source and target versions
- fail-fast on first invalid transformed document
- block backup overwrite unless forced explicitly

Reference patterns:
- backend/questionnaires/management/commands/normalise_questionnaire_sort_order.py
- backend/questionnaires/migrations/0004_backfill_questionnaire_code_from_name.py

### 5. Runtime Boundary

Keep strict runtime checks in the shared serializer path. Migration compatibility logic must remain internal to migration tooling and must not relax API request validation.

Target file:
- backend/api/serialisers.py

## Implementation Phases

### Phase 0: Baseline and Freeze
Dependencies: none.

Actions:
- Capture row counts grouped by schema_version for Questionnaire and Application.
- Freeze current schema version constants as cutover baseline.
- Document invariants and rollback expectations.

Exit criteria:
- Baseline report committed in migration runbook notes.
- Invariants agreed and recorded.

### Phase 1: Framework Foundations
Dependencies: Phase 0.

Actions:
- Add backup fields and corresponding DB migrations.
- Add versioned schema accessors.
- Add migration registries and path resolution.
- Add validation helpers against explicit target version.

Exit criteria:
- Local unit tests prove registry pathing and validation behaviours.

### Phase 2: Command Layer
Dependencies: Phase 1.

Actions:
- Implement report, dry-run, migrate, rollback, and clear-backup modes.
- Add transaction management and safety guardrails.
- Add deterministic migration_run_id handling.

Exit criteria:
- Command tests cover happy paths and failure rollback paths.

### Phase 3: Strict Runtime Protection
Dependencies: Phase 1. Parallelisable with Phase 2.

Actions:
- Verify strict current-version runtime behaviour remains unchanged.
- Add explicit API tests for rejection of old schema versions.

Exit criteria:
- API tests confirm strict policy remains intact.

### Phase 4: Fixtures and Regression Tests
Dependencies: Phases 2 and 3.

Actions:
- Update hardcoded schema_version fixtures.
- Add migration scenario fixtures.
- Extend serializer, API, command, and e2e tests for migration lifecycle.

Exit criteria:
- Targeted backend and frontend regression suites pass.

### Phase 5: Operational Runbook
Dependencies: Phase 4.

Actions:
- Document maintenance-window migration sequence.
- Document rollback sequence by migration_run_id.
- Document manual backup-retention approval process.

Target docs to update:
- docs/DEPLOYMENT.md
- docs/TESTING.md
- docs/BACKEND-CONVENTIONS.md

Exit criteria:
- Runbook reviewed and actionable for operators.

### Phase 6: First Migration Experiment
Dependencies: Phase 5.

Actions:
- Run a low-risk version-only migration experiment.
- Execute full lifecycle: report, dry-run, migrate, validate, rollback rehearsal.
- Record outcomes as canonical template for future schema migrations.

Exit criteria:
- Experiment completed with successful rollback rehearsal.

### Phase 7: First Real Schema Change Candidate
Dependencies: Phase 6.

Actions:
- Propose first shape-changing migration tied to questionnaire serialiser TODO direction.
- Produce a dedicated mapping specification before coding.

Exit criteria:
- Mapping spec approved before implementation begins.

## Verification Matrix

### Automated Verification
- Unit tests:
  - registry version pathing
  - transformation validation success and fail-fast behaviour
  - rollback restoration semantics
- Command tests:
  - report output correctness
  - dry-run no-write guarantee
  - migrate transaction success
  - rollback by run id
  - guard against backup overwrite
- API tests:
  - strict rejection of non-current schema_version post-cutover
- Regression tests:
  - application save and review paths
  - attachment linkage and rendering
  - selected e2e lifecycle paths

### Manual and Operational Verification
- Pre-migration report confirms expected version distribution.
- Dry-run confirms transform readiness with zero writes.
- Post-migration report confirms all target rows on destination version.
- Rollback rehearsal confirms precise payload restoration.

## Operational Runbook Summary

### Migration Window
1. Enter maintenance mode and block document writes.
2. Apply code and DB schema migrations.
3. Run migration command in migrate mode for target versions.
4. Run post-migration report and validity checks.
5. Exit maintenance mode only after checks pass.

### Rollback
1. Enter maintenance mode.
2. Run rollback mode with migration_run_id.
3. Run validation report to confirm restoration.
4. Exit maintenance mode only after rollback checks pass.

### Backup Lifecycle
- Preserve backup columns until manual approval.
- Use clear-backup mode only under explicit operational sign-off.

## Risks and Mitigations

- Risk: accidental overwrite of rollback backups.
  - Mitigation: default hard block when backup columns are already populated; force override only.
- Risk: hidden key-contract drift across layers.
  - Mitigation: keep key formats unchanged in framework phase and assert with regression tests.
- Risk: long lock times due to single transaction.
  - Mitigation: run within planned maintenance window and baseline dataset size before execution.

## Deliverables

Primary planning document:
- docs/SCHEMA-MIGRATION-PLAN.md

Supporting updates after implementation:
- docs/DEPLOYMENT.md
- docs/TESTING.md
- docs/BACKEND-CONVENTIONS.md

This document is the approved blueprint for implementing safe schema migration support across questionnaire and application documents.
