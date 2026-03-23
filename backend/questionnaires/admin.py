from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.db import transaction
from django.db.models import F, Max, Window
from django.db.models.functions import RowNumber

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import (
    Questionnaire,
)


@admin.register(Questionnaire)
class QuestionnaireAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = QuestionnaireForm
    # Don't show the "Show counts" on the filter facet
    show_facets = admin.ShowFacets.NEVER
    list_display = (
        "sort_order",
        "name",
        "version",
        "process",
        "sort_order_int",
    )
    list_filter = ("process",)
    readonly_fields = ("version", "created_at", "created_by")
    editable_fields = ("process", "name", "description", "document")
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

    def sort_order_int(self, obj):
        return obj.sort_order

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

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """
        Persist a questionnaire according to what actually changed.

        Three distinct code paths exist depending on what the editor modified:

        1. **New record** (``change=False``):
           Saved as-is; ``created_by`` is stamped and all other fields are
           taken directly from the submitted form.

        2. **Document changed** (``change=True``, ``document`` in changed fields):
           A new version row is cloned from the submitted data.  The version
           number is set to one above the current maximum for that
           ``(process, name)`` lineage so the history is never overwritten.
           If a move or rename was submitted at the same time, it is applied to
           the whole lineage first (see path 3) before the new version is
           inserted, ensuring the new row lands in the correct lineage.

        3. **Metadata only changed** (``change=True``, ``document`` unchanged):
           The existing row is updated in place — no new version is created.
           If ``process`` or ``name`` changed, the bulk-update below propagates
           those changes to every historical version of this questionnaire so
           the lineage identity stays consistent across all versions.
           ``description`` and ``sort_order`` changes are applied only to the
           latest version row (the one currently open in the form).

        This method is wrapped by ``@transaction.atomic`` so partial updates
        cannot leave the version history in an inconsistent state.
        """
        # ----------------------------------------------------------------
        # Path 1: brand-new questionnaire — stamp author and save directly.
        # ----------------------------------------------------------------
        if not change:
            obj.created_by = request.user
            return super().save_model(request, obj, form, change)

        # Lock the current database row so concurrent edits cannot race
        # between the read below and any subsequent writes in this block.
        original = Questionnaire.objects.select_for_update().get(pk=obj.pk)

        # Determine what kind of edit was submitted.
        process_or_name_changed = (
            original.process_id != obj.process_id or original.name != obj.name
        )
        document_changed = (
            "document" in form.changed_data
            and original.document != form.cleaned_data["document"]
        )

        # ----------------------------------------------------------------
        # Lineage propagation: move or rename across all historical versions.
        # Must run before the document-change path so the new version row
        # is inserted under the already-updated (process, name) identity.
        # ----------------------------------------------------------------
        if process_or_name_changed:
            Questionnaire.objects.filter(
                process_id=original.process_id,
                name=original.name,
            ).update(
                process_id=obj.process_id,
                name=obj.name,
            )

        # ----------------------------------------------------------------
        # Path 2: document edited — clone a new version row.
        # ----------------------------------------------------------------
        if document_changed:
            # Find the highest version currently in this lineage (after any
            # rename/move above) so the new version number is always N+1.
            max_version = (
                Questionnaire.objects.filter(
                    process_id=obj.process_id,
                    name=obj.name,
                ).aggregate(max_version=Max("version"))["max_version"]
                or 0
            )
            # Clear the pk so Django performs an INSERT rather than UPDATE,
            # creating a new row while leaving all previous versions intact.
            obj.version = max_version + 1
            obj.pk = None
            obj.created_by = request.user
            return super().save_model(request, obj, form, False)

        # ----------------------------------------------------------------
        # Path 3: metadata-only edit — update the existing row in place.
        # Restore immutable fields from the database so they cannot be
        # accidentally overwritten by stale form data.
        # ----------------------------------------------------------------
        obj.version = original.version
        obj.created_by = original.created_by
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
