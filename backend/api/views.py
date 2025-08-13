from applications.models import Application
from applications.serialisers import ApplicationSerialiser
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
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

    # def get_serializer_context(self):
    #     context = super().get_serializer_context()
    #     context["document_schema"] = "Some custom data"
    #     return context

    # @action(detail=True, methods=["post"])
    # def create(self, request):
    #     """
    #     Custom action to create an application.
    #     """
    #     # super().create(request)
    #     application = self.get_object()
    #     # Logic to handle submission
    #     # For example, changing the status or sending a notification

    #     import pdb; pdb.set_trace()

    #     # application.save()
    #     return Response({"status": "Application submitted successfully"})
