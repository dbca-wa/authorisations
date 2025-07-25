from django.contrib import admin, auth

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import Questionnaire

# Replace the default UserProfileAdmin to prevent deletion
admin.site.unregister(auth.models.User)


@admin.register(auth.models.User)
class UserProfileAdmin(auth.admin.UserAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    actions = None


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    form = QuestionnaireForm
    list_display = ("name", "slug", "version")
    ordering = (
        "slug",
        "-version",
    )
    readonly_fields = ("version", "created_at", "created_by")
    save_as = False
    save_as_continue = False

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
        # Existing object slug cannot be changed, (the name actually can)
        if obj is not None:
            return self.readonly_fields + ("slug", "name")

        return self.readonly_fields

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
        return super().get_queryset(request).distinct("slug")
