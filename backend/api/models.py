from dataclasses import dataclass

from django.conf import settings


@dataclass(init=False)
class ClientConfig:
    """
    Configuration for the client-side API.
    """

    api_base: str = "/api"
    csrf_header: str = settings.CSRF_HEADER_CLIENT
    csrf_token: str = None

    def __init__(self, csrf_token: str):
        self.csrf_token = csrf_token
        super().__init__()


