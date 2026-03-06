from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from processes.models import AuthorisationProcess


@admin.register(AuthorisationProcess)
class AuthorisationProcessAdmin(SortableAdminMixin, admin.ModelAdmin):
	list_display = ("name", "slug", "sort_order", "created_at", "updated_at")
	ordering = ("sort_order", "name")
	search_fields = ("name", "slug")

	def has_add_permission(self, request):
		return request.user.is_superuser

	def has_change_permission(self, request, obj=None):
		return request.user.is_superuser

	def has_delete_permission(self, request, obj=None):
		return request.user.is_superuser
