from applications.views import generic_template, resume_application
from django.contrib import admin
from django.urls import include, path
from dbnow.views import db_now_view
from home import home_page

urlpatterns = [
    path("", home_page),
    path("my-applications", generic_template, name="my-applications"),
    path("new-application", generic_template, name="new-application"),
    path("a/<slug:key>", resume_application, name="resume-application"),
    
    # Api
    path("api/", include("api.urls")),
    
    # Admin and admin tools
    path("dbnow", db_now_view, name="db-now"),
    path("admin/", admin.site.urls),
    path("admin_tools/", include("admin_tools.urls")),
]
