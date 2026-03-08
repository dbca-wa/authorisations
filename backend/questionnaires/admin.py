from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.db.models import F, Window
from django.db.models.functions import RowNumber

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Questionnaire


@admin.register(Questionnaire)
class QuestionnaireAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = QuestionnaireForm
    # Don't show the "Show counts" on the filter facet
    show_facets = admin.ShowFacets.NEVER
    list_display = ("sort_order", "name", "process", "version")
    list_filter = ("process",)
    readonly_fields = ("process", "name", "version", "created_at", "created_by")
    editable_fields = ("description", "document")
    # Keep sortable2 compatible: first field must be local/writable.
    ordering = ("sort_order",)

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
        """
        Override to return the latest version of each questionnaire.
         - Use Window function to rank versions per (process, name) group
         - Filter to keep only the latest version (rank=1)
         - Order by process sort_order, then questionnaire sort_order and name
         This ensures the admin list shows only the latest version of each questionnaire,
         ordered in a user-friendly way.
         Note: This approach may not be fully compatible with adminsortable2's drag-and-drop sorting,
         as it relies on database-level ordering. Adminsortable2 typically expects a simple ordering field.
        """

        return (
            super()
            .get_queryset(request)
            .select_related("process")
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

    @staticmethod
    def get_extra_model_filters(request):
        """
        Scope drag-and-drop reorder updates to the selected process filter.
        Without this, sortable operations may affect rows across all processes.
        """
        process_id = request.GET.get("process__id__exact")
        if process_id and process_id.isdigit():
            return {"process_id": int(process_id)}
        return {}
