from django.contrib import admin

from .models import Application, ApplicationAttachment
from .forms import ApplicationForm


class ApplicationAttachmentInline(admin.TabularInline):
    """Inline admin interface for application attachments."""

    model = ApplicationAttachment
    extra = 0
    readonly_fields = (
        "key",
        "answer",
        "created_at",
        "deleted_at",
    )
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
    list_display = ("owner", "questionnaire", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__username", "questionnaire__name")
    readonly_fields = (
        "key",
        "owner",
        "questionnaire",
        "status",
        "created_at",
        "updated_at",
        "submitted_at",
        "document",
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
