from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.middleware.csrf import get_token
from django.shortcuts import render


def my_applications(request):
    """View to display the user's applications."""

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    # Render the application form template with the provided name
    return render(
        request,
        "my-applications.html",
        {"config": ClientConfigSerialiser(config).data},
    )


def new_application(request):
    """View to handle the creation of a new application."""

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    return render(
        request,
        "new-application.html",
        {"config": ClientConfigSerialiser(config).data},
    )


def resume_application(request, key):
    """Resume an application based on the key provided in the URL."""
    # Verify application key access - return proper 404
    # if not Application.has_access(request.user, key):
    #     return render(request, "error.html", status=404)

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    # Render the application form template with the provided name
    return render(
        request,
        "resume-application.html",
        {"config": ClientConfigSerialiser(config).data},
    )
