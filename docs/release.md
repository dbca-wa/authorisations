# Release Guide

This document describes how semantic versioning works in this repository and the exact steps for creating a new release.

## Overview

The application uses semantic versioning in the format `MAJOR.MINOR.PATCH` (for example `1.0.0`).

The same version is consumed by four runtime/deployment touchpoints:

1. Production Docker image tag on `main` branch builds.
2. Kubernetes kustomize overlays (both prod and uat):
   - `kustomize/overlays/prod/kustomization.yaml` — synced to `VERSION` exactly.
   - `kustomize/overlays/uat/kustomization.yaml` — synced to `VERSION-uat` (pre-release suffix).
3. Frontend UI display (bottom of the side Drawer), sourced from backend bootstrap config.

## Single Source Of Truth

The canonical release version is the root `VERSION` file.

- File: `VERSION`
- Required format: `MAJOR.MINOR.PATCH`
- Example valid values:
  - `1.0.0`
  - `1.2.3`
  - `1.0.0-uat` (pre-release suffix for UAT environment)
  - `1.0.0-feature-name` (pre-release suffix for feature branch builds)
- Example invalid values:
  - `v1.0.0` (contains `v` prefix)
  - `1.0` (missing patch)
  - `1.0.0.0` (too many version segments)
  - `uat-1.0.0` (suffix must come after version, not before)
  - `1-0-0` (must use dots, not dashes, as separators)
  - `release-1.0.0` (custom suffixes not allowed; use scripts for pre-release tagging)

## How Versioning Is Wired

### 1. Production Docker tagging (`main` only)

In `azure-pipelines.yml`, the publish job calls `scripts/get_image_tag.py` to resolve the correct image tag based on the git branch and `VERSION` file.

The script applies the following tagging logic:

- On `main` branch:
  - Uses the semantic version from `VERSION` (e.g. `1.0.0`).
  - Docker image is pushed with tags:
    - `X.Y.Z`
    - `YYYY-MM-DD_HH.mm`
- On `uat` branch:
  - Appends `-uat` suffix to the semantic version for pre-release tracking (e.g. `1.0.0-uat`).
  - This allows Rancher to distinguish UAT deployments and avoid stale image cache issues.
  - Docker image is pushed with tags:
    - `X.Y.Z-uat`
    - `YYYY-MM-DD_HH.mm`
- On `feature/*` branches:
  - Appends the branch name as a pre-release suffix with `/` replaced by `-` (e.g. `1.0.0-auth-payments` for `refs/heads/feature/auth/payments`, or `1.0.0-experimental` for `refs/heads/feature/experimental`).
  - Docker image is pushed with tags:
    - `X.Y.Z-branch-name`
    - `YYYY-MM-DD_HH.mm`

Script: `scripts/get_image_tag.py`

Usage:

```bash
python3 scripts/get_image_tag.py <branch-ref>
```

Example:

```bash
python3 scripts/get_image_tag.py refs/heads/main    # outputs: 1.0.0
python3 scripts/get_image_tag.py refs/heads/uat     # outputs: 1.0.0-uat
python3 scripts/get_image_tag.py refs/heads/feature/auth/payments  # outputs: 1.0.0-auth-payments
```

### 2. Kubernetes kustomize image tags (prod and uat)

Both overlays are kept in sync atomically:

- Prod overlay (`kustomize/overlays/prod/kustomization.yaml`):
  - `images[].newTag` must match `VERSION` exactly (e.g. `1.0.0`).
- UAT overlay (`kustomize/overlays/uat/kustomization.yaml`):
  - `images[].newTag` must match `VERSION-uat` (pre-release format, e.g. `1.0.0-uat`).

The helper script synchronises both overlays together:

- Script: `scripts/sync_version.py`
- Sync mode (default): updates both prod and uat `newTag` fields to match their expected values based on `VERSION`.
- Check mode (`--check`): validates both overlays match their expected tags, fails if either differs.

CI runs `python3 scripts/sync_version.py --check` during validation to prevent drift in either overlay.

### 3. UI version display

The backend reads `VERSION` at startup and exposes it as `APP_VERSION` in Django settings. That value is injected into the client bootstrap config (`ClientConfig`) and rendered in the side Drawer footer in the frontend.

## Helper Scripts

This repository includes two Python scripts to manage versioning and tagging:

### `scripts/sync_version.py`

Synchronises both kustomize overlays (prod and uat) to match the canonical `VERSION` file, or validates they are aligned.

**Modes:**

- **Sync mode (default):** reads `VERSION`, updates both overlay newTag fields:
  - Prod overlay newTag → `VERSION` (e.g. `1.0.0`)
  - UAT overlay newTag → `VERSION-uat` (e.g. `1.0.0-uat`)
- **Check mode (`--check`):** validates both overlays match their expected tags based on `VERSION`, fails if either differs.

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

- Image tag suitable for Docker push (e.g. `1.0.0`, `uat`, `my-feature`).

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

The test suite includes 36 tests covering:
- VERSION file reading and validation (valid, invalid, missing, edge cases)
- Kustomize tag reading and writing (preserving structure, handling spacing)
- Image tag resolution for all branch types (main, uat, feature)- Overlay tag generation (prod and uat target tags)
- Kustomization path resolution for both overlays
- Multi-overlay sync and drift detection- Integration workflows (sync + check, end-to-end tagging)

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
   echo "X.Y.Z" > VERSION
   ```

3. Synchronise both kustomize overlays from `VERSION`.

   ```bash
   python3 scripts/sync_version.py
   ```

4. Confirm both overlays are correctly synced.

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
     - `kustomize/overlays/prod/kustomization.yaml` (prod overlay tag)
     - `kustomize/overlays/uat/kustomization.yaml` (uat overlay tag)
   - Include other release-adjacent updates as needed (for example release notes).

7. Open and merge the release PR to `main`.

8. After merge, let Azure Pipelines run on `main`.
   - Confirm Docker image tags include the new semantic version.
   - Confirm deployment manifest uses the same tag.

9. Verify the deployed UI shows the expected version string in the Drawer footer.

## Failure Modes And Recovery

### CI fails with version drift

Cause: One or both kustomize overlay tags do not match their expected values:
- Prod overlay tag does not match `VERSION`.
- UAT overlay tag does not match `VERSION-uat`.

Fix:

```bash
python3 scripts/sync_version.py
python3 scripts/sync_version.py --check
```

Commit the updated kustomize overlay files (prod and/or uat).

### CI fails with invalid VERSION format

Cause: `VERSION` does not match `MAJOR.MINOR.PATCH`.

Fix: rewrite `VERSION` using a valid value such as `1.2.3`.

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

- Do not edit kustomize overlay `newTag` fields manually. Always use `scripts/sync_version.py`.
- Keep `VERSION` as the only manual source of release version truth.
- Both prod and uat overlays are always kept in sync together; you cannot update one independently.
- Pre-release suffixes are reserved for environment-specific tagging: `-uat` for UAT overlays, and `-branch-name` for feature builds. Do not use `-rc`, `-alpha`, `-beta`, or other pre-release identifiers in the `VERSION` file itself.