#!/usr/bin/env python3
"""Test suite for versioning scripts: sync_version.py and get_image_tag.py"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import functions from scripts
from sync_version import (
    get_kustomization_path,
    get_target_tag,
    read_kustomize_tag,
    read_version,
    write_kustomize_tag,
)
from get_image_tag import (
    get_image_tag,
    read_version as read_version_image_tag,
)


class TestReadVersion:
    """Test VERSION file reading and validation."""

    def test_read_version_valid(self, tmp_path: Path) -> None:
        """Test reading a valid VERSION file."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")

        result = read_version(version_file)
        assert result == "1.2.3"

    def test_read_version_with_whitespace(self, tmp_path: Path) -> None:
        """Test that whitespace is stripped from VERSION."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("  1.2.3  \n")

        result = read_version(version_file)
        assert result == "1.2.3"

    def test_read_version_invalid_with_v_prefix(self, tmp_path: Path) -> None:
        """Test that VERSION with 'v' prefix is rejected."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("v1.2.3")

        with pytest.raises(ValueError, match="Expected format MAJOR.MINOR.PATCH"):
            read_version(version_file)

    def test_read_version_invalid_missing_patch(self, tmp_path: Path) -> None:
        """Test that VERSION without patch component is rejected."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2")

        with pytest.raises(ValueError, match="Expected format MAJOR.MINOR.PATCH"):
            read_version(version_file)

    def test_read_version_invalid_prerelease_suffix(self, tmp_path: Path) -> None:
        """Test that VERSION with pre-release suffix is rejected."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3-rc1")

        with pytest.raises(ValueError, match="Expected format MAJOR.MINOR.PATCH"):
            read_version(version_file)

    def test_read_version_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing VERSION file raises FileNotFoundError."""
        version_file = tmp_path / "VERSION"

        with pytest.raises(FileNotFoundError, match="VERSION file not found"):
            read_version(version_file)

    def test_read_version_large_numbers(self, tmp_path: Path) -> None:
        """Test that large version numbers are accepted."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("999.888.777")

        result = read_version(version_file)
        assert result == "999.888.777"


class TestKustomizeTag:
    """Test kustomize tag reading and writing."""

    def test_read_kustomize_tag_valid(self, tmp_path: Path) -> None:
        """Test reading newTag from a valid kustomization.yaml."""
        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text(
            "images:\n  - name: authorisations\n    newTag: 1.0.0\n"
        )

        result = read_kustomize_tag(kustomization_file)
        assert result == "1.0.0"

    def test_read_kustomize_tag_with_spacing(self, tmp_path: Path) -> None:
        """Test reading newTag with inconsistent spacing."""
        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text(
            "images:\n  - name: authorisations\n    newTag:   1.0.0  \n"
        )

        result = read_kustomize_tag(kustomization_file)
        assert result == "1.0.0"

    def test_read_kustomize_tag_not_found(self, tmp_path: Path) -> None:
        """Test that missing newTag raises ValueError."""
        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text("images:\n  - name: authorisations\n")

        with pytest.raises(ValueError, match="No newTag entry found"):
            read_kustomize_tag(kustomization_file)

    def test_read_kustomize_tag_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing kustomization file raises FileNotFoundError."""
        kustomization_file = tmp_path / "kustomization.yaml"

        with pytest.raises(FileNotFoundError, match="Kustomization file not found"):
            read_kustomize_tag(kustomization_file)

    def test_write_kustomize_tag_updates_in_place(self, tmp_path: Path) -> None:
        """Test that write_kustomize_tag updates the tag in-place."""
        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text(
            "images:\n  - name: authorisations\n    newTag: 1.0.0\n"
        )

        write_kustomize_tag(kustomization_file, "2.0.0")

        content = kustomization_file.read_text()
        assert "2.0.0" in content
        assert "1.0.0" not in content

    def test_write_kustomize_tag_preserves_structure(self, tmp_path: Path) -> None:
        """Test that write_kustomize_tag preserves the file structure."""
        kustomization_file = tmp_path / "kustomization.yaml"
        original_content = (
            "images:\n"
            "  - name: authorisations\n"
            "    newTag: 1.0.0\n"
            "    newName: my.registry.com/app\n"
        )
        kustomization_file.write_text(original_content)

        write_kustomize_tag(kustomization_file, "2.1.0")

        content = kustomization_file.read_text()
        assert "  - name: authorisations\n" in content
        assert "    newName: my.registry.com/app\n" in content
        assert "    newTag: 2.1.0\n" in content

    def test_write_kustomize_tag_no_newline(self, tmp_path: Path) -> None:
        """Test that write_kustomize_tag handles files without trailing newlines."""
        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text(
            "images:\n  - name: authorisations\n    newTag: 1.0.0"
        )

        write_kustomize_tag(kustomization_file, "2.0.0")

        content = kustomization_file.read_text()
        assert "2.0.0" in content


class TestOverlayTagGeneration:
    """Test target tag generation for different overlays."""

    def test_get_target_tag_prod(self) -> None:
        """Test that prod overlay gets the base version."""
        result = get_target_tag("prod", "1.2.3")
        assert result == "1.2.3"

    def test_get_target_tag_uat(self) -> None:
        """Test that uat overlay appends -uat suffix."""
        result = get_target_tag("uat", "1.2.3")
        assert result == "1.2.3-uat"

    def test_get_target_tag_uat_different_version(self) -> None:
        """Test uat suffix with different version numbers."""
        result = get_target_tag("uat", "2.5.0")
        assert result == "2.5.0-uat"

    def test_get_target_tag_invalid_overlay(self) -> None:
        """Test that invalid overlay raises ValueError."""
        with pytest.raises(ValueError, match="Unknown overlay"):
            get_target_tag("staging", "1.2.3")


class TestKustomizationPathResolution:
    """Test kustomization file path resolution for overlays."""

    def test_get_kustomization_path_prod(self, tmp_path: Path) -> None:
        """Test that prod overlay path is correctly resolved."""
        # Mock a root directory structure
        result = get_kustomization_path(tmp_path, "prod")
        assert result == tmp_path / "kustomize" / "overlays" / "prod" / "kustomization.yaml"

    def test_get_kustomization_path_uat(self, tmp_path: Path) -> None:
        """Test that uat overlay path is correctly resolved."""
        result = get_kustomization_path(tmp_path, "uat")
        assert result == tmp_path / "kustomize" / "overlays" / "uat" / "kustomization.yaml"

    def test_get_kustomization_path_invalid_overlay(self, tmp_path: Path) -> None:
        """Test that invalid overlay raises ValueError."""
        with pytest.raises(ValueError, match="Unknown overlay"):
            get_kustomization_path(tmp_path, "staging")


class TestGetImageTag:
    """Test Docker image tag resolution logic."""

    def test_get_image_tag_main_branch(self) -> None:
        """Test that main branch uses semantic version."""
        result = get_image_tag("refs/heads/main", "1.2.3")
        assert result == "1.2.3"

    def test_get_image_tag_uat_branch(self) -> None:
        """Test that uat branch appends -uat suffix to version."""
        result = get_image_tag("refs/heads/uat", "1.2.3")
        assert result == "1.2.3-uat"

    def test_get_image_tag_feature_branch_simple(self) -> None:
        """Test that feature branch appends -branch-name suffix to version."""
        result = get_image_tag("refs/heads/feature/new-endpoint", "1.2.3")
        assert result == "1.2.3-new-endpoint"

    def test_get_image_tag_feature_branch_with_slash(self) -> None:
        """Test that feature branch with nested path replaces '/' with '-' and appends to version."""
        result = get_image_tag("refs/heads/feature/auth/new-flow", "1.2.3")
        assert result == "1.2.3-auth-new-flow"

    def test_get_image_tag_feature_branch_multiple_slashes(self) -> None:
        """Test that multiple '/' are all replaced and suffixed to version."""
        result = get_image_tag("refs/heads/feature/team/feature/sub", "1.2.3")
        assert result == "1.2.3-team-feature-sub"

    def test_get_image_tag_uat_with_version_suffix(self) -> None:
        """Test that UAT branch creates proper semver pre-release tag."""
        result = get_image_tag("refs/heads/uat", "2.1.0")
        assert result == "2.1.0-uat"

    def test_get_image_tag_feature_with_version_suffix(self) -> None:
        """Test that feature branches create proper semver pre-release tags."""
        # Simple feature branch name
        result = get_image_tag("refs/heads/feature/experimental", "1.0.1")
        assert result == "1.0.1-experimental"
        
        # Nested feature branch name
        result = get_image_tag("refs/heads/feature/auth/payments", "1.0.1")
        assert result == "1.0.1-auth-payments"

    def test_get_image_tag_invalid_branch(self) -> None:
        """Test that unrecognised branches raise ValueError."""
        with pytest.raises(ValueError, match="Unrecognised branch"):
            get_image_tag("refs/heads/staging", "1.2.3")

    def test_get_image_tag_pull_request_branch(self) -> None:
        """Test that PR branches raise ValueError."""
        with pytest.raises(ValueError, match="Unrecognised branch"):
            get_image_tag("refs/pull/123/merge", "1.2.3")


class TestReadVersionImageTag:
    """Test VERSION reading function in get_image_tag.py"""

    def test_read_version_image_tag_valid(self, tmp_path: Path) -> None:
        """Test reading VERSION from get_image_tag module."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.0.0")

        result = read_version_image_tag(version_file)
        assert result == "1.0.0"

    def test_read_version_image_tag_invalid(self, tmp_path: Path) -> None:
        """Test that invalid VERSION raises in get_image_tag module."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("v1.0.0")

        with pytest.raises(ValueError):
            read_version_image_tag(version_file)


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_sync_and_check_workflow(self, tmp_path: Path) -> None:
        """Test the typical sync + check workflow."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("2.0.0")

        kustomization_file = tmp_path / "kustomization.yaml"
        kustomization_file.write_text("images:\n  - name: app\n    newTag: 1.0.0\n")

        # Initially out of sync
        assert read_kustomize_tag(kustomization_file) == "1.0.0"
        assert read_version(version_file) == "2.0.0"

        # Sync to VERSION
        write_kustomize_tag(kustomization_file, read_version(version_file))

        # Now they match
        assert read_kustomize_tag(kustomization_file) == "2.0.0"
        assert read_version(version_file) == "2.0.0"

    def test_image_tag_for_all_branch_types(self, tmp_path: Path) -> None:
        """Test image tag resolution for all branch types with pre-release suffixes."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.5.0")

        version = read_version_image_tag(version_file)

        # Main builds with semantic version
        assert get_image_tag("refs/heads/main", version) == "1.5.0"

        # UAT appends -uat suffix for pre-release tracking
        assert get_image_tag("refs/heads/uat", version) == "1.5.0-uat"

        # Feature branches append their name as suffix
        assert get_image_tag("refs/heads/feature/api-v2", version) == "1.5.0-api-v2"
        assert get_image_tag("refs/heads/feature/auth/login", version) == "1.5.0-auth-login"

    def test_multi_overlay_sync_prod_and_uat(self, tmp_path: Path) -> None:
        """Test syncing both prod and uat overlays with correct tag formats."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("2.3.1")

        # Create overlay directories
        prod_dir = tmp_path / "kustomize" / "overlays" / "prod"
        uat_dir = tmp_path / "kustomize" / "overlays" / "uat"
        prod_dir.mkdir(parents=True)
        uat_dir.mkdir(parents=True)

        # Create kustomization files
        prod_kustomization = prod_dir / "kustomization.yaml"
        uat_kustomization = uat_dir / "kustomization.yaml"
        prod_kustomization.write_text("images:\n  - name: app\n    newTag: 1.0.0\n")
        uat_kustomization.write_text("images:\n  - name: app\n    newTag: 1.0.0-uat\n")

        # Sync both overlays
        version = read_version(version_file)
        prod_target = get_target_tag("prod", version)
        uat_target = get_target_tag("uat", version)

        write_kustomize_tag(prod_kustomization, prod_target)
        write_kustomize_tag(uat_kustomization, uat_target)

        # Verify both are updated correctly
        assert read_kustomize_tag(prod_kustomization) == "2.3.1"
        assert read_kustomize_tag(uat_kustomization) == "2.3.1-uat"

    def test_overlay_tag_drift_detection(self, tmp_path: Path) -> None:
        """Test detecting version drift in different overlays."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.5.0")

        # Create overlay directories
        prod_dir = tmp_path / "kustomize" / "overlays" / "prod"
        uat_dir = tmp_path / "kustomize" / "overlays" / "uat"
        prod_dir.mkdir(parents=True)
        uat_dir.mkdir(parents=True)

        # Create kustomization files with outdated tags
        prod_kustomization = prod_dir / "kustomization.yaml"
        uat_kustomization = uat_dir / "kustomization.yaml"
        prod_kustomization.write_text("images:\n  - name: app\n    newTag: 1.4.0\n")
        uat_kustomization.write_text("images:\n  - name: app\n    newTag: 1.4.0-uat\n")

        # Detect drift
        version = read_version(version_file)
        prod_tag = read_kustomize_tag(prod_kustomization)
        uat_tag = read_kustomize_tag(uat_kustomization)

        assert prod_tag != version
        assert uat_tag != f"{version}-uat"
