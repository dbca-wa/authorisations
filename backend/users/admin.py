from django.contrib import admin, auth

from users.models import User

# Replace the default UserProfileAdmin to prevent deletion
# admin.site.unregister(User)


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    actions = None
