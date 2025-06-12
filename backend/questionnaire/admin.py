from django.contrib import admin, auth

from questionnaire.forms import QuestionnaireForm
from questionnaire.models import Questionnaire

# admin.site.register(Application)

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
    # search_fields = ("name", "slug")
    # list_filter = ('slug',)
    ordering = (
        "slug",
        "-version",
    )
    # exclude = ("version",)
    # readonly_fields = ("version", "created_at", "created_by")
    readonly_fields = ("version", "created_at", "created_by")
    # actions = [custom_action]
    save_as = False
    save_as_continue = False

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return True

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
        
        # self.fields["created_by"].initial = request.user
        # self.fields["created_by"].disabled = True
        # self.get_form(request).fields["created_by"].initial = request.user
        

        # replace the created_by field with the current user
        # self.form.instance.created_by = request.user

        return super().add_view(request, form_url, extra_context)

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     form.current_user = request.user
    #     return form

    # def get_changeform_initial_data(self, request):
    #     return {"created_by": request.user}

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + ("slug", "name")
            # return self.readonly_fields + ("slug", "name", "created_by")

        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        # If the object is being changed, increment the version
        if change:
            obj.version += 1
            obj.pk = None
            # obj.created_by = request.user

        # Newly created or versioned up
        if obj.pk is None:
            obj.created_by = request.user
        
        # import pdb; pdb.set_trace()

        # Save and return
        return super().save_model(request, obj, form, change)
