#!/usr/bin/env python3
"""Synchronise the canonical VERSION tag into kustomize overlays."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for sync and drift-check modes."""
    parser = argparse.ArgumentParser(
        description=(
            "Synchronise VERSION into both kustomize overlays (prod and uat) "
            "atomically, or check for version drift."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate kustomize tags match VERSION without modifying files.",
    )
    return parser.parse_args()


def read_version(version_file: Path) -> str:
    """Read and validate the canonical semantic version from VERSION."""
    if not version_file.is_file():
        raise FileNotFoundError(f"VERSION file not found: {version_file}")

    version = version_file.read_text(encoding="utf-8").strip()
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(
            f"Invalid version '{version}' in {version_file}. "
            "Expected format MAJOR.MINOR.PATCH."
        )
    return version


def get_kustomization_path(root_dir: Path, overlay: str) -> Path:
    """Return the kustomization.yaml path for the given overlay."""
    if overlay not in ("prod", "uat"):
        raise ValueError(f"Unknown overlay: {overlay}")
    return root_dir / "kustomize" / "overlays" / overlay / "kustomization.yaml"


def get_target_tag(overlay: str, version: str) -> str:
    """Generate the target image tag for the given overlay and version.
    
    Prod overlays use the base version (e.g. 1.0.0).
    UAT overlays append the -uat pre-release suffix (e.g. 1.0.0-uat).
    """
    if overlay == "prod":
        return version
    elif overlay == "uat":
        return f"{version}-uat"
    else:
        raise ValueError(f"Unknown overlay: {overlay}")


def read_kustomize_tag(kustomization_file: Path) -> str:
    """Extract the first newTag value from the production kustomization overlay."""
    if not kustomization_file.is_file():
        raise FileNotFoundError(f"Kustomization file not found: {kustomization_file}")

    for line in kustomization_file.read_text(encoding="utf-8").splitlines():
        if "newTag:" in line:
            _, value = line.split(":", 1)
            return value.strip()

    raise ValueError(f"No newTag entry found in {kustomization_file}")


def write_kustomize_tag(kustomization_file: Path, version: str) -> None:
    """Rewrite newTag in-place so manifests follow VERSION exactly."""
    lines = kustomization_file.read_text(encoding="utf-8").splitlines(keepends=True)

    updated_lines: list[str] = []
    replaced = False
    for line in lines:
        if not replaced and "newTag:" in line:
            prefix = line.split("newTag:", 1)[0]
            line_ending = "\n" if line.endswith("\n") else ""
            updated_lines.append(f"{prefix}newTag: {version}{line_ending}")
            replaced = True
            continue
        updated_lines.append(line)

    if not replaced:
        raise ValueError(f"No newTag entry found in {kustomization_file}")

    kustomization_file.write_text("".join(updated_lines), encoding="utf-8")


def main() -> int:
    """Run sync or check mode based on command-line arguments.
    
    Always processes both prod and uat overlays atomically to maintain
    version consistency across all environments.
    """
    args = parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    version_file = root_dir / "VERSION"

    try:
        canonical_version = read_version(version_file)
        any_drift = False

        # Always process both overlays atomically
        for overlay in ("prod", "uat"):
            kustomization_file = get_kustomization_path(root_dir, overlay)
            target_tag = get_target_tag(overlay, canonical_version)
            current_tag = read_kustomize_tag(kustomization_file)

            if args.check:
                if current_tag != target_tag:
                    print(
                        (
                            f"Version drift in {overlay} overlay: "
                            f"{kustomization_file} has '{current_tag}', "
                            f"expected '{target_tag}'."
                        ),
                        file=sys.stderr,
                    )
                    any_drift = True
                else:
                    print(f"✓ {overlay}: {target_tag}")

            else:  # sync mode
                if current_tag == target_tag:
                    print(f"✓ {overlay}: already {target_tag}")
                else:
                    write_kustomize_tag(kustomization_file, target_tag)
                    print(f"✓ {overlay}: updated to {target_tag}")

        if args.check:
            if any_drift:
                return 1
            print(f"Version check passed: {canonical_version}")
            return 0

        return 0

    except (FileNotFoundError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())