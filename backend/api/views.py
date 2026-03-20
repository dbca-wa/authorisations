import uuid

from applications.models import Application, ApplicationAttachment
from applications.serialisers import ApplicationSerialiser, AttachmentSerialiser
from django.db.models import BooleanField, Exists, F, OuterRef, Value, Window
from django.db.models.functions import RowNumber
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
        Return only the latest questionnaire version for each (process, name),
        then order for display by process and questionnaire sort order.
        """
        queryset = (
            self.filter_queryset(self.get_queryset())
            .annotate(
                _latest_rank=Window(
                    expression=RowNumber(),
                    partition_by=[F("process_id"), F("name")],
                    order_by=F("version").desc(),
                )
            )
            .filter(_latest_rank=1)
            .order_by("process__sort_order", "sort_order", "name")
        )

        serializer = self.get_serializer(queryset, many=True)
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

    def get_queryset(self):
        """Annotate each process with whether the current user can review it."""
        queryset = super().get_queryset()

        # Compute ``can_review`` at queryset level so the database can answer it
        # for the whole process list in one query. Doing this in the serializer
        # would push request-aware permission logic into presentation code and
        # risks per-row checks / N+1 queries.
        if not self.request.user.is_authenticated:
            # Anonymous users can never review; annotate a constant False so the
            # serializer still receives a stable field on every process row.
            return queryset.annotate(
                can_review=Value(False, output_field=BooleanField())
            )

        # Build an EXISTS subquery against the process<->group join table. If
        # any linked reviewer group matches one of the current user's groups,
        # the process is reviewable for that user.
        reviewer_group_links = AuthorisationProcess.reviewer_groups.through.objects.filter(
            authorisationprocess_id=OuterRef("pk"),
            group_id__in=self.request.user.groups.values("id"),
        )

        # Expose the result as a boolean annotation for direct serialisation.
        return queryset.annotate(can_review=Exists(reviewer_group_links))


