#!/usr/bin/env python3
"""Test suite for versioning scripts: sync_version.py and get_image_tag.py"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import functions from scripts
from sync_version import (
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


class TestGetImageTag:
    """Test Docker image tag resolution logic."""

    def test_get_image_tag_main_branch(self) -> None:
        """Test that main branch uses semantic version."""
        result = get_image_tag("refs/heads/main", "1.2.3")
        assert result == "1.2.3"

    def test_get_image_tag_uat_branch(self) -> None:
        """Test that uat branch uses 'uat' tag."""
        result = get_image_tag("refs/heads/uat", "1.2.3")
        assert result == "uat"

    def test_get_image_tag_feature_branch_simple(self) -> None:
        """Test that feature branch uses branch name."""
        result = get_image_tag("refs/heads/feature/new-endpoint", "1.2.3")
        assert result == "new-endpoint"

    def test_get_image_tag_feature_branch_with_slash(self) -> None:
        """Test that feature branch with nested path replaces '/' with '-'."""
        result = get_image_tag("refs/heads/feature/auth/new-flow", "1.2.3")
        assert result == "auth-new-flow"

    def test_get_image_tag_feature_branch_multiple_slashes(self) -> None:
        """Test that multiple '/' are all replaced."""
        result = get_image_tag("refs/heads/feature/team/feature/sub", "1.2.3")
        assert result == "team-feature-sub"

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
        """Test image tag resolution for all branch types."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.5.0")

        version = read_version_image_tag(version_file)

        # Main builds with semantic version
        assert get_image_tag("refs/heads/main", version) == "1.5.0"

        # UAT always uses 'uat'
        assert get_image_tag("refs/heads/uat", version) == "uat"

        # Feature branches use branch name
        assert get_image_tag("refs/heads/feature/api-v2", version) == "api-v2"
        assert get_image_tag("refs/heads/feature/auth/login", version) == "auth-login"
