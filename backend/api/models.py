from dataclasses import dataclass

from django.conf import settings


@dataclass(init=False)
class ClientConfig:
    """
    Configuration for the client-side API.
    """

    base_url: str = "/api/"
    csrf_header: str = settings.CSRF_HEADER_CLIENT
    csrf_token: str = None

    # def __new__(cls, csrf_token: str):
    #     print(csrf_token)
    #     return super().__new__(cls)

    def __init__(self, csrf_token: str):
        self.csrf_token = csrf_token
        super().__init__()


