# Release Guide

This document describes how semantic versioning works in this repository and the exact steps for creating a new release.

## Overview

The application uses semantic versioning in the format `vMAJOR.MINOR.PATCH` (for example `v1.0.0`).

The same version is consumed by three runtime/deployment touchpoints:

1. Production Docker image tag on `main` branch builds.
2. Production kustomize image tag in `kustomize/overlays/prod/kustomization.yaml`.
3. Frontend UI display (bottom of the side Drawer), sourced from backend bootstrap config.

## Single Source Of Truth

The canonical release version is the root `VERSION` file.

- File: `VERSION`
- Required format: `vMAJOR.MINOR.PATCH`
- Example valid values:
  - `v1.0.0`
  - `v1.2.3`
- Example invalid values:
  - `1.0.0` (missing `v`)
  - `v1.0` (missing patch)
  - `v1.0.0-rc1` (pre-release suffix currently not supported by validation)

## How Versioning Is Wired

### 1. Production Docker tagging (`main` only)

In `azure-pipelines.yml`, the publish job calls `scripts/get_image_tag.py` to resolve the correct image tag based on the git branch and `VERSION` file.

The script applies the following tagging logic:

- On `main` branch:
  - Uses the semantic version from `VERSION` (e.g. `v1.0.0`).
  - Docker image is pushed with tags:
    - `vX.Y.Z`
    - `YYYY-MM-DD_HH.mm`
- On `uat` branch:
  - Uses the static tag `uat`.
  - Docker image is pushed with tags:
    - `uat`
    - `YYYY-MM-DD_HH.mm`
- On `feature/*` branches:
  - Uses the branch name (after `refs/heads/feature/`) with `/` replaced by `-` (e.g. `my-feature` for `refs/heads/feature/my-feature`, or `auth-new-flow` for `refs/heads/feature/auth/new-flow`).
  - Docker image is pushed with tags:
    - `my-feature`
    - `YYYY-MM-DD_HH.mm`

Script: `scripts/get_image_tag.py`

Usage:

```bash
python3 scripts/get_image_tag.py <branch-ref>
```

Example:

```bash
python3 scripts/get_image_tag.py refs/heads/main    # outputs: v1.0.0
python3 scripts/get_image_tag.py refs/heads/uat     # outputs: uat
python3 scripts/get_image_tag.py refs/heads/feature/new-endpoint  # outputs: new-endpoint
```

### 2. Production kustomize image tag

The production overlay must match `VERSION` exactly:

- File: `kustomize/overlays/prod/kustomization.yaml`
- Field: `images[].newTag`

The helper script keeps this aligned:

- Script: `scripts/sync_version.py`
- Sync mode (default): updates prod `newTag` to match `VERSION`.
- Check mode (`--check`): fails if prod `newTag` differs from `VERSION`.

CI also runs `python3 scripts/sync_version.py --check` during validation to prevent drift.

### 3. UI version display

The backend reads `VERSION` at startup and exposes it as `APP_VERSION` in Django settings. That value is injected into the client bootstrap config (`ClientConfig`) and rendered in the side Drawer footer in the frontend.

## Helper Scripts

This repository includes two Python scripts to manage versioning and tagging:

### `scripts/sync_version.py`

Synchronises the production kustomize tag to match the canonical `VERSION` file, or validates they are aligned.

**Modes:**

- **Sync mode (default):** reads `VERSION`, updates `kustomize/overlays/prod/kustomization.yaml` newTag to match.
- **Check mode (`--check`):** reads `VERSION` and kustomize tag, fails if they differ.

**Usage:**

```bash
# Synchronise prod overlay tag to VERSION
python3 scripts/sync_version.py

# Validate no drift between VERSION and prod overlay
python3 scripts/sync_version.py --check
```

### `scripts/get_image_tag.py`

Resolves the Docker image tag for the current build based on git branch and `VERSION`.

**Inputs:**

- Git branch ref (e.g. `refs/heads/main`, `refs/heads/feature/my-feature`).
- `VERSION` file (read automatically from repo root).

**Outputs:**

- Image tag suitable for Docker push (e.g. `v1.0.0`, `uat`, `my-feature`).

**Usage:**

```bash
# Get tag for current branch (useful in CI)
python3 scripts/get_image_tag.py "$(git symbolic-ref --short HEAD)"

# Explicit branch ref
python3 scripts/get_image_tag.py refs/heads/main
```

### Testing

Both scripts are covered by a comprehensive test suite: `scripts/test_scripts.py`

Run tests locally with:

```bash
cd backend
poetry run pytest ../scripts/test_scripts.py -v
```

Or from the backend directory without poetry (if dependencies are installed):

```bash
cd scripts
pytest test_scripts.py -v
```

The test suite includes 25 tests covering:
- VERSION file reading and validation (valid, invalid, missing, edge cases)
- Kustomize tag reading and writing (preserving structure, handling spacing)
- Image tag resolution for all branch types (main, uat, feature)
- Integration workflows (sync + check, end-to-end tagging)

All tests use pytest fixtures and have no external dependencies beyond what is already in the backend's dev environment.

**CI Integration:**

Script tests are automatically run in the Azure Pipelines `BackendTests` job as part of the `Validate` stage, before running the main backend test suite.



Follow these steps in order when preparing a new production release.

1. Decide the semantic version bump.
   - `PATCH`: bug fixes and low-risk internal changes.
   - `MINOR`: backwards-compatible feature additions.
   - `MAJOR`: breaking or incompatible changes.

2. Update the canonical version.

   ```bash
   echo "vX.Y.Z" > VERSION
   ```

3. Synchronise production kustomize tag from `VERSION`.

   ```bash
   python3 scripts/sync_version.py
   ```

4. Confirm there is no version drift.

   ```bash
   python3 scripts/sync_version.py --check
   ```

5. Run tests before raising/reviewing the release PR.

   ```bash
   cd backend && poetry run pytest
   cd ../frontend && bun run test
   ```

6. Commit the release changes.
   - At minimum, expect:
     - `VERSION`
     - `kustomize/overlays/prod/kustomization.yaml`
   - Include other release-adjacent updates as needed (for example release notes).

7. Open and merge the release PR to `main`.

8. After merge, let Azure Pipelines run on `main`.
   - Confirm Docker image tags include the new semantic version.
   - Confirm deployment manifest uses the same tag.

9. Verify the deployed UI shows the expected version string in the Drawer footer.

## Failure Modes And Recovery

### CI fails with version drift

Cause: `kustomize/overlays/prod/kustomization.yaml` tag does not match `VERSION`.

Fix:

```bash
python3 scripts/sync_version.py
python3 scripts/sync_version.py --check
```

Commit the updated kustomize file.

### CI fails with invalid VERSION format

Cause: `VERSION` does not match `vMAJOR.MINOR.PATCH`.

Fix: rewrite `VERSION` using a valid value such as `v1.2.3`.

### UI shows unexpected version

Cause candidates:

1. `VERSION` was not updated before build.
2. Release branch/commit drifted from expected source.
3. Deployed environment is still running an older image.

Fix:

1. Confirm `VERSION` in the deployed commit.
2. Confirm pushed Docker tag and deployed manifest tag.
3. Redeploy the correct image tag if required.

## Operational Notes

- Do not edit the production `newTag` manually. Always use `scripts/sync_version.py`.
- Keep `VERSION` as the only manual source of release version truth.
- If pre-release identifiers (for example `-rc1`) are needed in future, update validation in one place (`scripts/sync_version.py`) and align pipeline checks accordingly.