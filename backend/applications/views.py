from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.middleware.csrf import get_token
from django.shortcuts import render
from questionnaires.models import Questionnaire, QuestionnaireSerialiser

from .models import Application


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

    # Fetch the latest version of questionnaires, grouped by slug
    # questionnaires = Questionnaire.objects.order_by("slug", "-version").distinct("slug")

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    return render(
        request,
        "new-application.html",
        {
            # "json_data": [QuestionnaireSerialiser(q).data for q in questionnaires],
            "config": ClientConfigSerialiser(config).data,
        },
    )


# def display_new_application(request, slug):
#     """Display a new application form for the questionnaire based on the `slug`
#     provided in the URL."""
#     # Find the questionnaire by slug
#     try:
#         questionnaire = Questionnaire.objects.filter(slug=slug).latest("version")
#     except Questionnaire.DoesNotExist:
#         # If the questionnaire does not exist, return a 404 error
#         return render(request, "error.html", status=404)

#     # Render the application form template with the provided name
#     return render(
#         request,
#         "questionnaire.html",
#         {"json_data": QuestionnaireSerialiser(questionnaire).data},
#     )


def resume_application(request, key):
    """Resume an application based on the key provided in the URL."""
    # Verify application key access
    # if not Application.has_access(request.user, key):
    #     return render(request, "error.html", status=404)

    # Get config with CSRF token
    config = ClientConfig(get_token(request))

    # Render the application form template with the provided name
    return render(
        request,
        "resume-application.html",
        {
            # "json_data": QuestionnaireSerialiser(application.questionnaire).data,
            "config": ClientConfigSerialiser(config).data,
        },
    )

