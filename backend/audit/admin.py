"""Admin interface for audit logs (read-only)."""

from django.contrib import admin

from .models import ApplicationAuditLog


@admin.register(ApplicationAuditLog)
class ApplicationAuditLogAdmin(admin.ModelAdmin):
    """Read-only admin interface for audit logs.

    Allows staff to view the audit trail of application status changes
    but prevents modification or deletion to maintain audit integrity.
    """

    list_display = (
        "application_id",
        "user",
        "prev_status",
        "next_status",
        "timestamp",
    )
    list_filter = ("next_status", "timestamp")
    search_fields = ("application__key", "user__email")
    readonly_fields = (
        "application",
        "user",
        "prev_status",
        "next_status",
        "timestamp",
    )
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        """Prevent manual entry of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs to maintain audit integrity."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs to maintain audit integrity."""
        return False
