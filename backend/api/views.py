import uuid

from applications.models import Application, ApplicationAttachment
from applications.serialisers import ApplicationSerialiser, AttachmentSerialiser
from processes.models import AuthorisationProcess
from processes.serialisers import AuthorisationProcessSerialiser
from questionnaires.models import Questionnaire, QuestionnaireSerialiser
from rest_framework import filters, mixins, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response


class ApplicationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A simple ViewSet for listing or retrieving applications.
    """

    queryset = Application.objects.all()
    serializer_class = ApplicationSerialiser
    lookup_field = "key"
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "options",
        "head",
    ]

    def get_queryset(self):
        """
        This view should return a list of all the applications
        for the currently authenticated user.
        """
        # Ensure users can only see their own applications
        return (
            super()
            .get_queryset()
            .select_related("owner", "questionnaire", "questionnaire__process")
            .filter(owner=self.request.user)
        )


class ApplicationFilterBackend(filters.BaseFilterBackend):
    """
    Filter that displays only attachments belonging to given application key.
    """

    def filter_queryset(self, request, queryset, view):
        application_key = request.query_params.get("application_key")
        if application_key:
            # Catch invalid UUIDs
            try:
                app_key_uuid = uuid.UUID(application_key)
            except ValueError as error:
                raise ValidationError(str(error))
            else:
                return queryset.filter(application__key=app_key_uuid)

        return queryset


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attachments for a specific application.
    """

    queryset = ApplicationAttachment.objects.all()
    serializer_class = AttachmentSerialiser
    lookup_field = "key"
    filter_backends = [ApplicationFilterBackend]
    http_method_names = [
        "get",
        "post",
        "delete",
        "patch",
        "options",
        "head",
    ]

    def get_queryset(self):
        """
        Only allow access to attachments of applications:
            * owned by the user
            * not deleted
        """
        return ApplicationAttachment.objects.select_related(
            "application", "application__owner"
        ).filter(
            application__owner=self.request.user,
            is_deleted=False,
        )

    def perform_destroy(self, instance: ApplicationAttachment):
        # defensive check
        if instance.application.owner != self.request.user:
            raise NotFound("Attachment not found.")
        instance.soft_delete()


class QuestionnaireViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving questionnaires.
    """

    queryset = Questionnaire.objects.select_related("process")
    serializer_class = QuestionnaireSerialiser
    lookup_field = "id"
    http_method_names = [
        "get",
        "options",
        "head",
    ]

    def list(self, request, *args, **kwargs):
        """
        Override to return the latest version of each questionnaire.
        """
        queryset = self.filter_queryset(self.get_queryset())
        # Group by slug and get the latest version
        distinct_slugs = queryset.order_by("process_id", "name", "-version").distinct("process_id", "name")

        serializer = self.get_serializer(distinct_slugs, many=True)
        return Response(serializer.data)


class AuthorisationProcessViewSet(viewsets.ReadOnlyModelViewSet):
    """A simple ViewSet for listing or retrieving authorisation processes."""

    queryset = AuthorisationProcess.objects.all()
    serializer_class = AuthorisationProcessSerialiser
    lookup_field = "slug"
    http_method_names = [
        "get",
        "options",
        "head",
    ]


