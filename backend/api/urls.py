from django.urls import include, path
from rest_framework import routers

from .views import ApplicationViewSet, QuestionnaireViewSet, AttachmentViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter(trailing_slash=False)
router.register("applications", ApplicationViewSet)
router.register("questionnaires", QuestionnaireViewSet)
router.register("attachments", AttachmentViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
]
