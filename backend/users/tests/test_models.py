"""Unit tests for custom user model basics."""

import pytest

from users.models import User


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_user_str_representation_defaults_to_username():
    """Keep user string representation aligned with Django AbstractUser username output."""
    user = User.objects.create_user(username="alice", password="testpass123")

    assert str(user) == "alice"


def test_user_can_store_email_and_staff_flags():
    """Persist common auth fields required by admin and permission checks."""
    user = User.objects.create_user(
        username="reviewer",
        password="testpass123",
        email="reviewer@example.com",
        is_staff=True,
    )

    reloaded = User.objects.get(pk=user.pk)

    assert reloaded.email == "reviewer@example.com"
    assert reloaded.is_staff is True
