from django.shortcuts import render

# Display an application form based on the name provided in the URL
def display_new_application(request, name):
    # Render the application form template with the provided name
    return render(request, "questionnaire.html", {"name": name})
