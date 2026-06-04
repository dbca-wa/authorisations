"""Cache-control middleware for global no-store defaults.

Django does not provide a built-in middleware that applies ``never_cache``
semantics to every response. This middleware fills that gap by applying
``add_never_cache_headers`` globally, while still allowing per-view overrides.
"""

from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin


class GlobalNeverCacheMiddleware(MiddlewareMixin):
    """Apply no-cache headers to responses that do not already define caching.

    The middleware intentionally skips responses that already include a
    ``Cache-Control`` header so view-level decorators such as
    ``@cache_control(...)`` can override the global default behaviour.
    """

    def process_response(self, request, response):
        """Ensure each response is non-cacheable unless a view set its own policy."""
        # Respect explicit per-view cache directives so decorators can override.
        if "Cache-Control" in response:
            return response

        # Match Django's never_cache semantics via the official utility.
        add_never_cache_headers(response)
        return response
