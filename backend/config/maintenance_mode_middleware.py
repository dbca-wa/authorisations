"""Maintenance mode middleware for safe deployments and database migrations.

When MAINTAINANCE_MODE is enabled, all requests receive a maintenance page
or API-appropriate response. The setting is checked efficiently on each request.
"""

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.deprecation import MiddlewareMixin


class MaintenanceModeMiddleware(MiddlewareMixin):
    """Return maintenance page for all requests when maintenance mode is enabled.

    This middleware is placed early in the middleware stack (after SecurityMiddleware)
    to intercept all request types uniformly with minimal overhead when disabled.

    Configuration:
    - Set MAINTAINANCE_MODE=True in environment to enable
    - Default: False (disabled)

    Behaviour when enabled:
    - API requests (/api/*) return JSON 503 Service Unavailable
    - All other requests return HTML maintenance page

    Performance note:
    - When disabled (typical case): single boolean check in process_request is all that runs
    - Settings lookups are cached internally by Django, so checking on each request is efficient
    """

    def process_request(self, request):
        """Check maintenance mode and return appropriate response if enabled.
        
        Returns None if maintenance mode is disabled (allows request to proceed normally).
        Returns HTTP 503 response if maintenance mode is enabled.
        """
        # Early exit: lightweight check when maintenance mode is disabled (typical case).
        if not settings.MAINTAINANCE_MODE:
            return None

        # Detect API endpoints: return JSON 503
        if request.path.startswith("/api/"):
            return JsonResponse(
                {"error": "Service Unavailable", "detail": "The service is currently under maintenance."},
                status=503,
            )

        # All other requests: return HTML maintenance page
        # This covers HTML pages, file downloads, and any non-API endpoints.
        html_content = render_to_string("maintenance.html")
        response = HttpResponse(html_content, status=503)
        response["Content-Type"] = "text/html; charset=utf-8"
        return response
