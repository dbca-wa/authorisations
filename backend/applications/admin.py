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
    search_fields = ("owner__username", "questionnaire__name")
    readonly_fields = (
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
