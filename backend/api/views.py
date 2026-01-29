import os

from applications.models import Application
from applications.serialisers import ApplicationSerialiser, AttachmentSerialiser
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from questionnaires.models import Questionnaire, QuestionnaireSerialiser
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
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

    def get_queryset(self):
        """
        This view should return a list of all the applications
        for the currently authenticated user.
        """
        # Ensure users can only see their own applications
        return super().get_queryset().filter(owner=self.request.user)

    @action(
        detail=True,
        methods=["get", "post", "delete"],
        serializer_class=AttachmentSerialiser,
    )
    def attachments(self, request, key=None):
        """
        Custom endpoint to manage files for a specific application.
        
        - `GET /applications/{key}/attachments/`: List all attachments for the application.
        - `GET /applications/{key}/attachments/{uuid}/`: Download a specific file.
        - `DELETE /applications/{key}/attachments/{uuid}/`: Delete a specific file.
        - `POST /applications/{key}/attachments/`: Upload a new file (with question index reference).
        """

        # This gets the parent Application instance
        application = self.get_object()
        
        # Handle file upload
        if request.method == "POST":
            return self._upload_file(request, application)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _upload_file(self, request, application: Application) -> Response:
        # Validate file upload first
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]

        # Use a private media directory (should be set in Django settings)
        private_media_root = getattr(settings, "PRIVATE_MEDIA_ROOT", None)
        if not private_media_root or not os.path.exists(private_media_root):
            return Response(
                {"error": "PRIVATE_MEDIA_ROOT is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Organize files by application key
        app_folder = os.path.join(private_media_root, str(application.key))
        os.makedirs(app_folder, exist_ok=True)

        # Save the file using FileSystemStorage
        fs = FileSystemStorage(location=app_folder)
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = os.path.join(
            "/private-media", str(application.key), filename
        )  # Not public, just for reference

        # Optionally: store file metadata in DB here

        return Response(
            {"status": "file uploaded", "filename": filename, "path": file_url},
            status=status.HTTP_201_CREATED,
        )


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
