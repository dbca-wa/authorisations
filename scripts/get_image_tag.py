#!/usr/bin/env python3
"""Resolve the Docker image tag based on VERSION and git branch."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


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


def get_image_tag(branch: str, version: str) -> str:
    """Resolve Docker image tag based on branch and version.
    
    Main branch: use semantic version tag (e.g. 1.0.0).
    UAT branch: use 'uat'.
    Feature branches: use branch name with '/' replaced by '-'.
    """
    if branch == "refs/heads/main":
        return version
    elif branch == "refs/heads/uat":
        return "uat"
    elif branch.startswith("refs/heads/feature/"):
        feature_name = branch.replace("refs/heads/feature/", "").replace("/", "-")
        return feature_name
    else:
        raise ValueError(f"Unrecognised branch: {branch}")


def main() -> int:
    """Read VERSION and branch, output the resolved image tag."""
    if len(sys.argv) < 2:
        print(
            "Usage: get_image_tag.py <branch>",
            file=sys.stderr,
        )
        print(
            "  <branch>  Git branch ref (e.g. refs/heads/main, refs/heads/feature/foo)",
            file=sys.stderr,
        )
        return 1

    branch = sys.argv[1]
    root_dir = Path(__file__).resolve().parents[1]
    version_file = root_dir / "VERSION"

    try:
        version = read_version(version_file)
        image_tag = get_image_tag(branch, version)
        print(image_tag)
        return 0

    except (FileNotFoundError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
