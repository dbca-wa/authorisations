from applications.views import (
    download_application,
    download_attachment,
    generic_template,
    resume_application,
)
from dbnow.views import db_now_view
from django.contrib import admin
from django.urls import include, path
from home import home_page

urlpatterns = [
    path("", home_page),
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
    path("dbnow", db_now_view, name="db-now"),
    path("admin/", admin.site.urls),
    path("admin_tools/", include("admin_tools.urls")),
]
