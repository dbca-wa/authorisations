from django.contrib import admin

from .models import Application
from .forms import ApplicationForm


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for managing applications."""
    
    form = ApplicationForm
    list_display = ("owner", "questionnaire", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__username", "questionnaire__name")
    readonly_fields = (
        "key", "owner", 
        "questionnaire", "status",
        "created_at", "updated_at", "submitted_at",
    )
    editable_fields = ("document", )
    
    fieldsets = (
        # This is the first fieldset, appearing at the top
        (None, { 
            'fields': readonly_fields,
        }),
        # A subsequent fieldset for editable fields
        ('Editable Fields', { 
            'fields': editable_fields,
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    