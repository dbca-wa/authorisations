from applications.models import Application
from applications.serialisers import ApplicationSerialiser
from rest_framework import mixins, viewsets, filters
from rest_framework.response import Response

from questionnaires.models import Questionnaire, QuestionnaireSerialiser
from rest_framework.exceptions import NotFound


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

    # Ensure users can only see their own applications
    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(owner=self.request.user)


class VersionFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        # If we received a ?version query parameter, filter the queryset.
        version = view.get_request_version()
        if version:
            return queryset.filter(version=version)

        return queryset


class QuestionnaireViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving applications.
    """

    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerialiser

    lookup_field = "slug"
    filter_backends = [VersionFilterBackend]

    def get_request_version(self) -> int | None:
        try:
            return int(self.request.query_params.get("version"))
        except (TypeError, ValueError):
            return None

    def get_object(self):
        """
        Override to get the object based on the slug.
        """
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}

        # Check if the "version" filter was applied
        version = self.get_request_version()

        if version:
            try:
                return queryset.get(**filter_kwargs)
            except Questionnaire.DoesNotExist as error:
                raise NotFound(str(error))

        # No (integer) version number requested, return the latest
        return queryset.filter(**filter_kwargs).latest("version")
    
    def list(self, request, *args, **kwargs):
        """
        Override to return the latest version of each questionnaire.
        """
        queryset = self.filter_queryset(self.get_queryset())
        # Group by slug and get the latest version
        distinct_slugs = queryset.order_by("slug", "-version").distinct("slug")

        serializer = self.get_serializer(distinct_slugs, many=True)
        return Response(serializer.data)
