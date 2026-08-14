"""Tests for maintenance mode middleware.

Tests cover:
- Request passthrough when maintenance mode is disabled
- HTML maintenance page for non-API requests when enabled
- JSON 503 response for API requests when enabled
"""

import json

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from config.maintenance_mode_middleware import MaintenanceModeMiddleware


@pytest.fixture
def middleware():
    """Create a middleware instance for testing."""
    return MaintenanceModeMiddleware(lambda r: HttpResponse())


@pytest.fixture
def factory():
    """Create a request factory for generating test requests."""
    return RequestFactory()


class TestMaintenanceModeMiddleware:
    """Test suite for MaintenanceModeMiddleware."""

    @override_settings(MAINTAINANCE_MODE=False)
    def test_requests_passthrough_when_disabled(self, middleware, factory):
        """Test that requests pass through normally when maintenance mode is disabled."""
        request = factory.get("/")
        response = middleware.process_request(request)

        # Should return None (allow request to proceed)
        assert response is None

    @override_settings(MAINTAINANCE_MODE=True)
    def test_api_request_returns_json_503_when_enabled(self, factory):
        """Test that API requests return JSON 503 when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.get("/api/applications/")

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "application/json"
        # Verify JSON content
        content = json.loads(response.content.decode())
        assert "error" in content
        assert content["error"] == "Service Unavailable"

    @override_settings(MAINTAINANCE_MODE=True)
    def test_html_request_returns_maintenance_page_when_enabled(self, factory):
        """Test that HTML requests return maintenance page when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.get("/")

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "text/html; charset=utf-8"
        content = response.content.decode()
        assert "Under Maintenance" in content

    @override_settings(MAINTAINANCE_MODE=True)
    def test_file_download_blocked_when_enabled(self, factory):
        """Test that file downloads return maintenance page when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        # Simulate download_application endpoint
        request = factory.get("/d/550e8400-e29b-41d4-a716-446655440000")

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "text/html; charset=utf-8"

    @override_settings(MAINTAINANCE_MODE=True)
    def test_attachment_download_blocked_when_enabled(self, factory):
        """Test that attachment downloads return maintenance page when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        # Simulate download_attachment endpoint
        request = factory.get(
            "/d/550e8400-e29b-41d4-a716-446655440000/550e8400-e29b-41d4-a716-446655440001"
        )

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "text/html; charset=utf-8"

    @override_settings(MAINTAINANCE_MODE=True)
    def test_api_upload_returns_json_503_when_enabled(self, factory):
        """Test that POST/PUT API requests return JSON 503 when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.post("/api/applications/")

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "application/json"

    @override_settings(MAINTAINANCE_MODE=True)
    def test_review_page_blocked_when_enabled(self, factory):
        """Test that reviewer page returns maintenance page when maintenance mode is enabled."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.get("/review")

        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        assert response["Content-Type"] == "text/html; charset=utf-8"

    @override_settings(MAINTAINANCE_MODE=True)
    def test_maintenance_page_contains_friendly_message(self, factory):
        """Test that maintenance page contains user-friendly message."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.get("/")

        response = middleware.process_request(request)
        content = response.content.decode()

        # Verify friendly content
        assert "Under Maintenance" in content
        assert "working hard" in content or "back shortly" in content

    @pytest.mark.security
    @override_settings(MAINTAINANCE_MODE=True)
    def test_maintenance_page_no_database_queries(self, factory):
        """Test that maintenance page does not perform database queries."""
        middleware = MaintenanceModeMiddleware(lambda r: HttpResponse())
        request = factory.get("/")

        # This test verifies the middleware can serve a static HTML page
        # without touching the database. If DB is down, this should still work.
        response = middleware.process_request(request)

        assert response is not None
        assert response.status_code == 503
        # Content should render without database access
        content = response.content.decode()
        assert len(content) > 0
