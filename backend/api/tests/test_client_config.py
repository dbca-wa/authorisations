from django.conf import settings
from django.test import SimpleTestCase

from api.models import ClientConfig
from api.serialisers import ClientConfigSerialiser


class ClientConfigSerialiserTests(SimpleTestCase):
    """Verify client bootstrap config includes version metadata."""

    def test_serialiser_includes_app_version_from_settings(self):
        """Expose the canonical app version in the frontend bootstrap payload."""
        config = ClientConfig(csrf_token="token-123")

        serialised = ClientConfigSerialiser(config).data

        self.assertEqual(serialised["app_version"], settings.APP_VERSION)
