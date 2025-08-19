from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.middleware.csrf import get_token
from django.shortcuts import render


def generic_vite_template(request, title):
    """Generic view to render a Vite template with a title."""

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    # Render the application form template with the provided name
    return render(
        request,
        "vite.html",
        {
            "config": ClientConfigSerialiser(config).data,
            "title": title,
        },
    )


def my_applications(request):
    """View to display the user's applications."""

    return generic_vite_template(request, "My applications")


def new_application(request):
    """View to handle the creation of a new application."""
    
    return generic_vite_template(request, "New application")


def resume_application(request, key):
    """Resume an application based on the key provided in the URL."""
    # Verify application key access - return proper 404
    # if not Application.has_access(request.user, key):
    #     return render(request, "error.html", status=404)
    
    return generic_vite_template(request, "Resume application")
