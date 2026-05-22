"""Unit tests for process domain model behaviour."""

import pytest
from django.db import IntegrityError

from processes.models import AuthorisationProcess


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_authorisation_process_str_representation():
    """Render process rows using the stable slug-prefixed representation."""
    process = AuthorisationProcess.objects.create(
        slug="s40",
        name="Section 40",
        description="Section 40 authorisation process",
        sort_order=1,
    )

    assert str(process) == "[s40] Section 40"


def test_authorisation_process_default_ordering_uses_sort_order():
    """Order process querysets by sort_order so UI process cards stay curated."""
    later = AuthorisationProcess.objects.create(
        slug="later",
        name="Later",
        description="Later process",
        sort_order=2,
    )
    earlier = AuthorisationProcess.objects.create(
        slug="earlier",
        name="Earlier",
        description="Earlier process",
        sort_order=1,
    )

    ordered_slugs = list(AuthorisationProcess.objects.values_list("slug", flat=True))

    assert ordered_slugs == [earlier.slug, later.slug]


def test_authorisation_process_slug_is_unique():
    """Protect process identity by enforcing uniqueness on slug."""
    AuthorisationProcess.objects.create(
        slug="dup",
        name="Duplicate one",
        description="First",
        sort_order=1,
    )

    with pytest.raises(IntegrityError):
        AuthorisationProcess.objects.create(
            slug="dup",
            name="Duplicate two",
            description="Second",
            sort_order=2,
        )
