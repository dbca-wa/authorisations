# Frontend Conventions

Development patterns and best practices for the frontend codebase.

**See [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md) for the comprehensive feature development checklist, testing requirements, and common commands.**

## Code comment conventions

- Every new function — regardless of size — must have a docstring comment directly above or inside it that explains **what the function does** and why it exists
  - For TypeScript/React: use a `/** ... */` JSDoc block before the function
- Every critical part within a function (non-obvious logic, guards, fallbacks, side effects) must have one or two single-line comments explaining the intent, not just restating the code
- Comments should explain **why**, not just **what**

## Application flow and UX

- New application flow is process-centric:
  - Present processes first
  - Then present questionnaire choices under each process
- Keep frontend type contracts aligned with API payloads:
  - Process identifiers and questionnaire identifiers must be explicit and unambiguous

## Component structure and patterns

### Component definitions
- Prefer React component definitions as `const` (for example `const MyComponent = () => { ... }`) rather than `function` declarations unless there is a clear technical reason to do otherwise
- Prefer frontend function expressions assigned to `const` (including hooks and local helpers) rather than `function` declarations unless there is a clear technical reason (for example hoisting requirements)

### Exports and imports
- Prefer explicit named exports/imports over default exports/imports for project modules where practicable, to make refactoring safer and imports more consistent
- Group imports by style with a single blank line separating default imports from named/type imports:
  - First block: default imports (no curly braces), for example `import React from "react"` or `import Box from "@mui/material/Box"`
  - Second block: named and type imports (with curly braces), for example `import { useState } from "react"` or `import type { AlertColor } from "@mui/material/Alert"`
  - This separation is purely organisational — it makes the import block easier to scan at a glance and reflects the technical distinction between default and named exports

## Localisation

- Use `dayjs` for dates with `en-au` locale

## Package manager policy

**Mandatory for all contexts (development, CI, production):**
- Use `npm` exclusively for all frontend package management: dev server, linting, testing, building, and dependency management
- Commands: `npm run dev`, `npm run lint`, `npm run test:unit`, `npm run build`, and `npm install package-name`
- `package-lock.json` is committed to version control and used by all environments

**Why npm:**
- **Consistency across environments**: npm's deterministic resolution ensures identical dependency trees in development, CI, and production
- **Audit compliance**: npm is the industry standard for production environments and passes corporate/regulatory audits
- **No version drift**: committed `package-lock.json` guarantees identical versions everywhere
- **Bun risks**: Bun resolves optional and peer dependencies differently than npm, causing version mismatches (e.g., yaml@1.10.2 vs 2.9.0). This incompatibility breaks the requirement for identical versions across environments.
- Prevents accidental npm usage that would undermine consistency

---

**See [FEATURE-DEVELOPMENT.md](FEATURE-DEVELOPMENT.md) for comprehensive development guidelines, testing, and command reference.**

## Application sorting patterns

### Reusable sorting utilities
- Application list pages (`MyApplications`, `Assessment`) use a reusable sorting system through `src/components/layout/main/applicationUtils.tsx`
- Sort options (type: `SortOrderOption`): `"application_type"` (Application Type), `"submitted_newest"` (Submitted: Newest), `"submitted_oldest"` (Submitted: Oldest), `"created_newest"` (Created: Newest), `"created_oldest"` (Created: Oldest), `"updated_newest"` (Updated: Newest), `"updated_oldest"` (Updated: Oldest)
- Hierarchical sorting: `"application_type"` sorts by `process_sort_order` (primary) then `questionnaire_sort_order` (secondary)
- Date-based sorting:
  - `"submitted_newest"`/`"submitted_oldest"` sort by submission date (`submitted_at` field). Unsubmitted applications (with `submitted_at === null`) sort to the end. These options are conditionally displayed only when applications with `submitted_at !== null` exist
  - `"created_newest"`/`"created_oldest"` sort by creation date
  - `"updated_newest"`/`"updated_oldest"` sort by modification date
- The `sortApplications(applications, sortOrder)` utility function is self-contained and requires no external lookups
- Helper functions for conditional display:
  - `hasSubmittedApplications(applications)` - returns true if any application has `submitted_at !== null`
  - `getAvailableSortOptions(applications)` - returns filtered list of sort options, excluding `submitted_*` options when no applications are submitted
- All sort preference persistence is handled via `localStorage` using page-specific keys (for example `"my-applications-sort-order"`, `"assessment-sort-order"`)
- Each page can specify its own default sort order via `getInitialSortOrder(storageKey, defaultSortOrder)` parameter:
  - `MyApplications` defaults to `"updated_newest"` (most recent changes shown first)
  - `Assessment` defaults to `"submitted_oldest"` (oldest submissions reviewed first)

### ApplicationSortControl component
- Reusable dropdown component for selecting sort order on any application list page
- Props:
  - `sortOrder` (current selection)
  - `onChange` (callback when selection changes)
  - `controlId` (unique HTML id for accessibility)
  - `availableOptions` (optional: array of visible sort options for conditional rendering; if omitted, all options are shown)
- Component automatically displays sort options with user-friendly labels
- Visibility of sort options is typically controlled by passing filtered `availableOptions` based on application data state

---

**See [README.md](README.md) for the documentation index.**
