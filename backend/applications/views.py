from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.http import FileResponse
from django.middleware.csrf import get_token
from django.shortcuts import render

from .models import Application, ApplicationAttachment

# Prepare a standard 404 response
RESPONSE_404 = render(
    None,
    "error.html",
    status=404,
    context={
        "message": "404 - Not found",
        "details": "The requested resource was not found on this server.",
    },
)


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
    # Fetch the application object
    try:
        application = Application.objects.get(key=key)
    except Application.DoesNotExist:
        return RESPONSE_404

    # Verify application key access
    if application.has_access(request.user) is False:
        return RESPONSE_404

    return generic_template(request)


def download_attachment(request, appKey, attachmentKey):
    """Download an attachment based on the application and attachment key provided in the URL."""
    # Fetch the attachment object
    try:
        attachment = ApplicationAttachment.objects.select_related(
            "application", "application__owner"
        ).get(
            application__key=appKey,
            key=attachmentKey,
            is_deleted=False,
        )
    except ApplicationAttachment.DoesNotExist:
        return RESPONSE_404

    # Verify that the user has access to this application
    if attachment.application.has_access(request.user) is False:
        return RESPONSE_404

    # Serve the file
    return FileResponse(attachment.file, as_attachment=False, filename=attachment.name)
