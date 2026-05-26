# Contributing

## Purpose

This project supports DBCA authorisation workflows. Contributions should preserve regulatory, audit, and ownership requirements while improving the codebase in small, reviewable changes.

## Before you contribute

- Raise an issue or start a discussion for substantial changes before opening a pull request.
- Keep changes focused. Avoid unrelated refactors in the same contribution.
- Preserve existing security, ownership, and version-history behaviour unless the change explicitly requires otherwise.

## Development expectations

- Use British English spelling in code comments and documentation.
- Follow the repository guidance in `.github/copilot-instructions.md`.
- Keep backend and frontend API contracts aligned when changing request or response payloads.
- Update documentation and notices files when behaviour, dependencies, or release obligations change.

## Testing

Backend:

```bash
cd backend
poetry run pytest
```

Frontend:

```bash
cd frontend
bun run test
```

Run any narrower tests needed for the changed area before opening a pull request.

## Commit and pull request guidance

- Write clear commit messages that describe the functional change.
- Include tests or explain why tests were not practicable.
- Update `THIRD_PARTY_NOTICES.md` when adding, removing, or materially changing dependencies.
- Do not commit secrets, production credentials, or sensitive personal information.

## Contribution licensing

Unless explicitly agreed otherwise in writing, contributions submitted to this repository are made under the same licence as the repository, as described in `LICENSE`.