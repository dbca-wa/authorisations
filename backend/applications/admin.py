from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from .models import Application, ApplicationAttachment, ApplicationStatus
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
    search_fields = ("owner__username", "questionnaire__name", "questionnaire__code", "questionnaire__process__slug")
    readonly_fields = (
        "internal_id",
        "key",
        "owner",
        "questionnaire",
        "status",
        "created_at",
        "updated_at",
        "submitted_at",
        "reset_button",
        # "document",
    )
    editable_fields = ()

    fieldsets = (
        # This is the first fieldset, appearing at the top
        (
            None,
            {
                "fields": readonly_fields[:-1],  # Exclude reset_button from main fieldset
            },
        ),
        # A subsequent fieldset for editable fields
        (
            "Editable Fields",
            {
                "fields": editable_fields,
            },
        ),
        # Actions fieldset for the reset button
        (
            "Actions",
            {
                "fields": ("reset_button",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Prefetch questionnaire and process to avoid N+1 queries on the list view."""
        return (
            super()
            .get_queryset(request)
            .select_related("owner", "questionnaire", "questionnaire__process")
        )

    def get_search_results(self, request, queryset, search_term):
        """
        Override search to support exact internal_id matching.
        Allows users to search by the full internal_id (e.g., "s40-serk-21" or
        the submitted form "s40-serk-21/26-03").
        """
        # First, try to match the search_term as an exact internal_id.
        # Format is "{process_slug}-{questionnaire_code}-{application_id}" with an
        # optional submitted-at suffix of "/{yy}-{mm}" on submitted applications.
        # Strip the suffix before parsing so the numeric ID is always at the end
        # of the base segment — otherwise rsplit would split the date instead.
        if search_term:
            base = search_term.split("/", 1)[0]
            parts = base.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                app_id = int(parts[1])
                try:
                    app = Application.objects.select_related(
                        "questionnaire", "questionnaire__process"
                    ).get(id=app_id)
                    # Verify the full internal_id matches the original search term
                    # to prevent a partial-prefix collision (e.g. two processes
                    # whose slugs share the same numeric suffix).
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
        # Allow superusers to POST for the reset button; otherwise read-only
        if request.user.is_superuser and request.method == "POST":
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def reset_button(self, obj):
        """Display a button to reset a submitted application to draft status.

        The button is only visible if the application is in SUBMITTED status.
        Clicking it POSTs back to the detail view with a _reset_to_draft parameter.
        """
        if not obj or obj.status != ApplicationStatus.SUBMITTED:
            return ""

        return mark_safe(
            '<form method="post" style="display:inline">'
            '<button type="submit" name="_reset_to_draft" class="button" style="background-color:#ba2121">'
            'Reset to Draft'
            '</button>'
            '</form>'
        )

    reset_button.short_description = "Reset Application"

    def response_change(self, request, obj):
        """Handle the reset button submission before normal response logic."""
        if "_reset_to_draft" in request.POST:
            obj.reset_to_draft()
            self.message_user(
                request,
                f"Application {obj.internal_id} has been reset to DRAFT status. "
                f"The submitted_at timestamp has been cleared.",
                level=messages.SUCCESS,
            )
            # Return to the same object view after reset
            return super().response_change(request, obj)

        return super().response_change(request, obj)
