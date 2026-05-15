"""Minimal Playwright E2E placeholder test."""

import pytest


@pytest.mark.e2e
def test_playwright_hello_world_placeholder():
    """Provide a guaranteed-pass baseline E2E test while scaffolding is introduced."""
    assert "hello world" == "hello world"
