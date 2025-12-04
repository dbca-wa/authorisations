from django.contrib import admin

from questionnaires.forms import QuestionnaireForm
from questionnaires.models import (
    Questionnaire,
    QuestionnaireMembership,
    QuestionnairePermission,
)


@admin.register(QuestionnairePermission)
class QuestionnairePermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "created_at")
    search_fields = ("codename", "name", "description")
    ordering = ("codename",)


@admin.register(QuestionnaireMembership)
class QuestionnaireMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "questionnaire", "created_at")
    search_fields = (
        "user__email",
        "user__username",
        "questionnaire__name",
        "questionnaire__slug",
    )
    filter_horizontal = ("permissions",)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    form = QuestionnaireForm
    list_display = ("name", "slug", "version")
    ordering = (
        "slug",
        "-version",
    )
    readonly_fields = ("version", "created_at", "created_by", "slug")
    editable_fields = ("name", "description", "document")

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

        # Slug to be defined once; when creating a new record
        if obj is None:
            readonly_fields.remove("slug")

        return readonly_fields

    def get_fieldsets(self, request, obj=None):
        # If "slug" is not readonly, add it to editable fields
        readonly_fields = self.get_readonly_fields(request, obj)
        editable_fields = list(self.editable_fields)

        if "slug" not in readonly_fields:
            editable_fields.insert(0, "slug")

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
        return super().get_queryset(request).distinct("slug")


