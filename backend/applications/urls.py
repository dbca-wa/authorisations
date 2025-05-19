from django.urls import path

from .views import display_new_application

urlpatterns = [
    path("<slug:name>", display_new_application),
]