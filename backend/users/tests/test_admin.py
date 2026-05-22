"""Unit tests for custom user admin safety behaviour."""

import pytest
from django.contrib.admin.sites import AdminSite

from users.admin import UserAdmin
from users.models import User


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_user_admin_disables_delete_permission(rf):
    """Prevent admin-side user deletion to protect historical ownership links."""
    site = AdminSite()
    admin = UserAdmin(User, site)
    request = rf.get("/admin/users/user/")

    assert admin.has_delete_permission(request) is False


def test_user_admin_disables_bulk_actions():
    """Disable bulk actions to avoid accidental mass user operations."""
    site = AdminSite()
    admin = UserAdmin(User, site)

    assert admin.actions is None
