from django.contrib import admin

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Questionnaire


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    form = QuestionnaireForm
    # Don't show the "Show counts" on the filter facet
    show_facets = admin.ShowFacets.NEVER
    list_display = ("name", "process", "version")
    list_filter = ("process",)
    ordering = (
        "process_id",
        "name",
        "-version",
    )
    readonly_fields = ("process", "name", "version", "created_at", "created_by")
    editable_fields = ("description", "document")

    save_as = False
    save_as_continue = False

    fieldsets = (
        # This is the first fieldset, appearing at the top
        (
            None,
            {
                "fields": readonly_fields,  # Include your read-only fields here
            },
        ),
        # A subsequent fieldset for editable fields
        (
            "Editable Fields",
            {
                "fields": editable_fields,
            },
        ),
    )

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        extra_context["show_save"] = True

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        extra_context["show_save"] = True

        return super().add_view(request, form_url, extra_context)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)

        # Process to be defined once; when creating a new record
        if obj is None:
            readonly_fields.remove("process")
            readonly_fields.remove("name")

        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        # If "process" is not readonly, add it to editable fields
        readonly_fields = self.get_readonly_fields(request, obj)
        editable_fields = list(self.editable_fields)

        if "process" not in readonly_fields:
            editable_fields.insert(0, "process")
            editable_fields.insert(1, "name")

        return (
            (
                None,
                {
                    "fields": readonly_fields,
                },
            ),
            (
                "Editable Fields",
                {
                    "fields": tuple(editable_fields),
                },
            ),
        )

    def save_model(self, request, obj, form, change):
        # If the object is being changed, increment the version
        if change:
            obj.version += 1
            obj.pk = None

        # Newly created or version up
        if obj.pk is None:
            obj.created_by = request.user

        # Save and return
        return super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).distinct("process_id", "name")


# APPLICATION_TYPES = {
#     "NEW_APPLICATION": "Start a new application if your project; there WILL be animals to be handled or trapped and does NOT involve death of an animal as a deliberate measure",
#     "RENEWAL": "Apply for a renewal if you already have an active authorisation and want to continue with the same project after the current authorisation expires.",
#     "OBSERVATION_ONLY": "Apply for an observation-only authorisation if the project will NOT have any animals to be handled or trapped at all.",
#     "DEATH_AS_AN_ENDPOINT": "Start with a death-as-an-endpoint application if you are applying for an authorisation to use animals that have died as an endpoint.",
# }