from django.shortcuts import render

from questionnaire.models import Questionnaire


def display_new_application(request, slug):
    """Display a new application form for the questionnaire based on the `slug`
    provided in the URL."""
    # Find the questionnaire by slug
    try:
        questionnaire = Questionnaire.objects.filter(slug=slug).latest("version")
    except Questionnaire.DoesNotExist:
        # If the questionnaire does not exist, return a 404 error
        return render(request, "404.html", status=404)

    # Render the application form template with the provided name
    return render(
        request,
        "questionnaire.html",
        {"questionnaire": questionnaire.serialised},
    )
