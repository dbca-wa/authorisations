from django.shortcuts import render

from questionnaires.models import Questionnaire


def my_applications(request):
    """View to display the user's applications."""

    # Fetch the user's applications from the database

    # Render the application form template with the provided name
    return render(
        request,
        "my-applications.html",
        {"applications": []},
    )


def new_application(request):
    """View to handle the creation of a new application."""

    # Fetch the latest version of questionnaires, grouped by slug
    questionnaires = Questionnaire.objects.order_by("slug", "-version").distinct("slug")

    return render(
        request,
        "new-application.html",
        {"json_data": [q.serialised for q in questionnaires]},
    )


def display_new_application(request, slug):
    """Display a new application form for the questionnaire based on the `slug`
    provided in the URL."""
    # Find the questionnaire by slug
    try:
        questionnaire = Questionnaire.objects.filter(slug=slug).latest("version")
    except Questionnaire.DoesNotExist:
        # If the questionnaire does not exist, return a 404 error
        return render(request, "404.html", status=404)

    print(f"User: {request.user.is_authenticated} - {request.user.username}")

    # Render the application form template with the provided name
    return render(
        request,
        "questionnaire.html",
        {"json_data": questionnaire.serialised},
    )
