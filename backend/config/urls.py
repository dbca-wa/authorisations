from applications.views import display_new_application, my_applications, new_application
from django.contrib import admin
from django.urls import include, path
from dbnow.views import db_now_view
from home import home_page

urlpatterns = [
    path("", home_page),
    path("my-applications", my_applications, name="my-applications"),
    path("new-application", new_application, name="new-application"),
    path("q/<slug:slug>", display_new_application, name="questionnaire"),
    
    # Api
    path("api/", include("api.urls")),
    
    # Admin and admin tools
    path("dbnow", db_now_view, name="db-now"),
    path("admin/", admin.site.urls),
    path("admin_tools/", include("admin_tools.urls")),
]
