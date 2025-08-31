from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.middleware.csrf import get_token
from django.shortcuts import render


def generic_template(request):
    """Generic view to render a Vite (SPA) template."""

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    # Render the application form template with the provided name
    return render(
        request,
        "vite.html",
        {"config": ClientConfigSerialiser(config).data},
    )


def resume_application(request, key):
    """Resume an application based on the key provided in the URL."""
    # Verify application key access - return proper 404
    # if not Application.has_access(request.user, key):
    #     return render(request, "error.html", status=404)

    return generic_template(request)
