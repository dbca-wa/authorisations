# JSON Schema Migration Framework - Internal Extraction and Public Release Plan

## Executive Summary

This plan confirms the approved direction:

1. Extract the migration framework internally first.
2. Validate it with both questionnaires and applications.
3. Externalise publicly only after dual-app stability is proven.

This sequencing maximises safety and quality while still delivering open-source benefits.

## Confirmed Strategy Decisions

- We will not externalise immediately.
- We will create an internally independent plugin-style package first.
- We will adapt questionnaires first (parity), then applications.
- We will publish externally after two stable release cycles using the shared internal package.

---

## Dependency Policy (Confirmed)

## Core plugin dependencies (hard requirement)

- Django
- jsonschema

No other runtime dependency is required for the plugin core.

## Explicitly excluded from core plugin dependencies

- djangorestframework
- django-jsonform
- other framework-specific runtime packages

## DRF integration approach

DRF integration remains supported, but only as a consumer-side pattern:

- The host application keeps its own serializer mixin and raises DRF ValidationError.
- The plugin provides framework-agnostic validation utilities and structured error results.
- If DRF helper code is ever added, it must be optional and isolated (for example, separate extras or adapter package), not in core dependencies.

---

## Schema Version Storage Decision Analysis

Current implementation stores schema_version inside the JSON document root.

The project is open to refactoring to a dedicated model field (for example, schema_version as IntegerField or CharField).

## Option A - Version inside JSONField (current model)

### Pros

- Easiest adoption for other projects: no model migration required.
- Works with existing JSON payloads and schema definitions.
- Keeps document self-describing when exported or moved.
- Simplifies backward compatibility for projects already versioning inside JSON.

### Cons

- Version querying/indexing may be less efficient on large datasets.
- Version extraction is tied to JSON key stability.
- Slightly weaker database-level constraints.

## Option B - Dedicated database field (schema_version column)

### Pros

- Stronger query performance and indexing.
- Cleaner filtering and mixed-version detection.
- Easier to enforce constraints at the database/model level.
- Decouples migration state from document structure.

### Cons

- Requires model migrations and data backfill.
- Harder drop-in adoption for external users.
- Dual-write/consistency concerns during transition.

## Open-source acceptability and predictability

From an open-source plugin perspective, the most acceptable design is:

- Support both storage strategies via configuration.
- Default to in-document version for easiest onboarding.
- Provide first-class support for dedicated DB field for performance-focused teams.

This avoids forcing adopters into a schema refactor while still supporting robust database-native version tracking.

## Recommendation for this repository

Use a staged approach:

1. Keep in-document schema_version as canonical during extraction and dual-app adoption (faster delivery, lower immediate risk).
2. Introduce optional dedicated DB field support in the internal plugin design now.
3. After both apps are stable on shared framework, decide whether to migrate this repository to dedicated field.

If the team wants stronger operational querying early, move to dedicated DB field after internal extraction parity is complete, not before.

For the current implementation cycle, schema_version remains inside JSON data because this is already working and stable in production. The externalised module will be designed so version-source behaviour can be configured in a future release (for example, keeping JSON-based versioning or switching to a dedicated model field) without rewriting migration orchestration.

---

## Target Internal Package Design

```text
backend/schema_migration_framework/
  __init__.py
  config.py
  exceptions.py
  types.py
  core/
    loader.py
    pathing.py
    validator.py
    executor.py
    versioning.py
  commands/
    base.py
  adapters/
    django_models.py
```

## Version source abstraction (critical)

The framework must abstract where schema version is read/written:

- document_key mode: read/write document[schema_version]
- model_field mode: read/write model.schema_version

Both modes use the same migration execution engine.

---

## Internal Extraction Roadmap

## Phase 0 - Baseline and Contracts (2 to 3 days)

1. Freeze existing questionnaires command behaviour and outputs.
2. Freeze parity test baseline from existing test suite.
3. Document strict invariants (atomicity, idempotency, rollback, frozen schemas).

Exit criteria:

- Baseline approved.
- Parity checklist agreed.

## Phase 1 - Internal Framework Package (3 to 4 days)

1. Create internal package structure.
2. Move generic loader/pathing/validator logic.
3. Implement versioning abstraction for both storage modes.
4. Add unit tests for core primitives.

Exit criteria:

- Core tests passing.
- No app switched yet.

## Phase 2 - Questionnaires Adoption (4 to 5 days)

1. Replace questionnaires local internals with framework adapters.
2. Keep existing command names and UX unchanged.
3. Keep serializer behaviour unchanged (host app raises DRF exceptions).
4. Add contract tests for command output parity.

Exit criteria:

- Existing questionnaires tests pass.
- Command behaviour parity confirmed.

## Phase 3 - Applications Adoption (4 to 5 days)

1. Register applications model with the same internal framework.
2. Implement app migrations and command wrappers.
3. Align runtime schema-version validation through existing API serializer patterns.
4. Add focused tests for application migrate, rollback, status, dry-run, and mixed-version states.

Exit criteria:

- Applications path fully working and tested.
- No duplicated migration orchestration logic remains.

## Phase 4 - Hardening and Operational Validation (3 to 4 days)

1. Add failure-mode tests and rollback rehearsals.
2. Add performance checks for version distribution queries.
3. Validate both version storage modes in test matrix.

Exit criteria:

- Reliability gates passed.
- Operational handbook updates complete.

## Phase 5 - Public Externalisation (3 to 4 days)

1. Publish standalone repository.
2. Keep core dependencies to Django + jsonschema.
3. Add clear configuration examples for both version storage modes.
4. Document DRF integration as optional consumer pattern.

Exit criteria:

- Public package installable.
- Documentation complete and accurate.

---

## Test Strategy (Internal Before Public)

1. Unit tests:
   - loader, pathing, validator, executor, version resolvers.
2. Contract tests:
   - questionnaires command outputs and behaviour.
3. Integration tests:
   - end-to-end migrate and rollback flows in both apps.
4. Storage-mode tests:
   - document_key mode and model_field mode.
5. Failure-mode tests:
   - mixed versions, invalid transforms, precondition mismatch.

---

## Go/No-Go Criteria for Public Release

Go only if all are true:

1. Questionnaires and applications both run through the internal framework.
2. Two stable release cycles with no migration regressions.
3. Core plugin dependencies remain Django + jsonschema only.
4. Both version storage modes are documented and tested.

---

## Immediate Execution Steps

1. Start Phase 0 baseline freeze.
2. Implement internal package with version source abstraction.
3. Switch questionnaires to framework-backed execution.
4. Switch applications using same framework.
5. Perform hardening and only then externalise.

---

## Conclusion

The approved path is internal-first extraction with dual-app validation, followed by public release. The plugin core remains intentionally minimal (Django + jsonschema). Schema version storage should be supported in both in-document and dedicated-field modes to maximise predictability, adoption ease, and long-term operational robustness.
