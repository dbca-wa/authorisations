from django.contrib import admin

from .models import Application, ApplicationAttachment
from .forms import ApplicationForm


class ApplicationAttachmentInline(admin.TabularInline):
    """Inline admin interface for application attachments."""

    model = ApplicationAttachment
    extra = 0
    fields = (
        "question",
        "name",
        "created_at",
        "is_deleted",
        "deleted_at",
    )
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for managing applications."""

    form = ApplicationForm
    inlines = [ApplicationAttachmentInline]
    list_display = (
        "internal_id",
        "questionnaire",
        "questionnaire__process",
        "status",
        "owner",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "created_at",
        "updated_at",
        "questionnaire__process",
        "questionnaire__name",
    )
    search_fields = ("owner__username", "questionnaire__name", "questionnaire__code", "questionnaire__process__slug", "id")
    readonly_fields = (
        "internal_id",
        "key",
        "owner",
        "questionnaire",
        "status",
        "created_at",
        "updated_at",
        "submitted_at",
        # "document",
    )
    editable_fields = ()

    fieldsets = (
        # This is the first fieldset, appearing at the top
        (
            None,
            {
                "fields": readonly_fields,
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

    def get_search_results(self, request, queryset, search_term):
        """
        Override search to support exact internal_id matching.
        Allows users to search by the full internal_id (e.g., "s40-serk-21").
        """
        # First, try to match the search_term as an exact internal_id.
        # Extract the application ID from the end of the internal_id string.
        # Format is "{process_slug}-{questionnaire_code}-{application_id}".
        # The application_id is always numeric and at the end.
        if search_term:
            # Try to extract numeric app ID from the end (last component after dash)
            parts = search_term.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                app_id = int(parts[1])
                try:
                    app = Application.objects.select_related(
                        "questionnaire", "questionnaire__process"
                    ).get(id=app_id)
                    # Verify the full internal_id matches the search term
                    if app.internal_id == search_term:
                        queryset = queryset.filter(id=app_id)
                        return queryset, False
                except Application.DoesNotExist:
                    pass

        # Fall back to the default search on configured search_fields
        return super().get_search_results(request, queryset, search_term)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
