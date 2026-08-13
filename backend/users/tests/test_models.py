"""Unit tests for custom user model basics."""

import pytest
from django.contrib.auth.models import Group

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


def test_is_reviewer_returns_false_for_unauthenticated_user():
    """Unauthenticated users are not reviewers."""
    user = User.objects.create_user(username="inactive-user", password="testpass123", is_active=False)

    assert user.is_reviewer() is False


def test_is_reviewer_returns_false_for_user_without_reviewer_groups(user):
    """Authenticated users without reviewer group membership are not reviewers."""
    assert user.is_reviewer() is False


def test_is_reviewer_returns_true_when_user_is_member_of_reviewer_group(user, questionnaire_factory):
    """User is a reviewer when their group is in a process's reviewer_groups."""
    # Create a reviewer group and add user to it
    reviewer_group = Group.objects.create(name="test-reviewers")
    user.groups.add(reviewer_group)

    # Create a questionnaire (which has a process) with this group as reviewer
    questionnaire = questionnaire_factory()
    questionnaire.process.reviewer_groups.add(reviewer_group)

    assert user.is_reviewer() is True


def test_is_reviewer_returns_false_for_user_in_non_reviewer_group(user, questionnaire_factory):
    """User is not a reviewer when their group is not a process's reviewer_group."""
    # Create a non-reviewer group and add user to it
    other_group = Group.objects.create(name="other-group")
    user.groups.add(other_group)

    # Create a questionnaire with a different reviewer group
    reviewer_group = Group.objects.create(name="actual-reviewers")
    questionnaire = questionnaire_factory()
    questionnaire.process.reviewer_groups.add(reviewer_group)

    assert user.is_reviewer() is False
