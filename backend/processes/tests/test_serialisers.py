"""Unit tests for process serialiser behaviour."""

import pytest

from processes.models import AuthorisationProcess
from processes.serialisers import AuthorisationProcessSerialiser


pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_authorisation_process_serialiser_includes_expected_read_fields():
    """Expose stable read fields required by process listing views."""
    process = AuthorisationProcess.objects.create(
        slug="s45",
        name="Section 45",
        description="Section 45 authorisation process",
        sort_order=5,
    )
    setattr(process, "can_review", True)

    serialised = AuthorisationProcessSerialiser(process).data

    assert serialised["slug"] == "s45"
    assert serialised["name"] == "Section 45"
    assert serialised["description"] == "Section 45 authorisation process"
    assert serialised["sort_order"] == 5
    assert serialised["can_review"] is True


def test_authorisation_process_serialiser_rejects_write_to_read_only_fields():
    """Keep process API serialisation output-only for immutable endpoint contracts."""
    serialiser = AuthorisationProcessSerialiser(
        data={
            "slug": "new-proc",
            "name": "Should fail",
            "description": "Read-only test",
            "sort_order": 1,
            "can_review": True,
        }
    )

    assert serialiser.is_valid()
    assert serialiser.validated_data == {}
