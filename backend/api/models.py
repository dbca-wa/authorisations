from dataclasses import dataclass, field
from typing import List

from django.conf import settings


@dataclass(init=False)
class ClientConfig:
    """
    Configuration for the client-side API.
    """

    api_base: str = "/api"
    csrf_header: str = settings.CSRF_HEADER_CLIENT
    csrf_token: str = None
    upload_max_size: int = settings.UPLOAD_MAX_SIZE
    # Use a default_factory so we don't bind a mutable list at class-level.
    # Copy the settings list to avoid accidental shared-mutation.
    upload_mime_types: List[str] = field(
        default_factory=lambda: list(settings.UPLOAD_MIME_TYPES)
    )

    def __init__(self, csrf_token: str):
        self.csrf_token = csrf_token
        super().__init__()
