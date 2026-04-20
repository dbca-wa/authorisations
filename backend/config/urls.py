from applications.views import (
    download_application,
    download_attachment,
    generic_template,
    resume_application,
)
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from home import home_page

urlpatterns = [
    # Home page — commented out until the home page view is ready for production.
    # path("", home_page),
    # Redirect root to the main authenticated entry point in the meantime.
    path("", RedirectView.as_view(url="/my-applications", permanent=False)),
    path("my-applications", generic_template, name="my-applications"),
    path("new-application", generic_template, name="new-application"),
    path("assessment", generic_template, name="assessment"),
    path("a/<uuid:key>", resume_application, name="resume-application"),
    path("d/<uuid:appKey>", download_application, name="download-application"),
    path(
        "d/<uuid:appKey>/<uuid:attachmentKey>",
        download_attachment,
        name="download-attachment",
    ),
    # Api
    path("api/", include("api.urls")),
    # Admin and admin tools
    path("admin/", admin.site.urls),
    path("admin_tools/", include("admin_tools.urls")),
]
