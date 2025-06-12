from django.urls import path

from .views import display_new_application

urlpatterns = [
    path("<slug:slug>", display_new_application, name="new_application"),
]