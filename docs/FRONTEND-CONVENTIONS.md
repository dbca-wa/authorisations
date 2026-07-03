# Frontend Conventions

Development patterns and best practices for the frontend codebase.

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

## Development workflows

### Frontend commands
- Package manager policy:
  - Use Bun for local development workflows because it is faster and supports npm-compatible scripts
  - Use npm for UAT, production, and CI environments to keep deployment/runtime behaviour consistent
- Run dev server (local development): `cd frontend && bun run dev`
- Build (UAT/production/CI): `cd frontend && npm run build`
- Lint (UAT/production/CI): `cd frontend && npm run lint`

---

**See [README.md](README.md) for the documentation index.**
