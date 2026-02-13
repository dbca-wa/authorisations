from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser
from django.http import FileResponse
from django.middleware.csrf import get_token
from django.shortcuts import render

from applications.models import ApplicationAttachment


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
        return render(request, "error.html", status=404)

    # Verify that the user has access to this application
    if attachment.application.has_access(request.user) is False:
        return render(
            request,
            "error.html",
            status=404,
            context={
                "message": "404 - Not found",
                "details": "The attachment file you are looking for does not exist.",
            },
        )

    # Serve the file
    return FileResponse(attachment.file, as_attachment=True, filename=attachment.name)
