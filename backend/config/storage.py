from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """
    Custom storage class for handling uploaded files.
    Files stored using this storage backend are not publicly accessible.
    """

    def __init__(self, *args, **kwargs):
        # Save it to the PRIVATE_MEDIA_ROOT - not MEDIA_ROOT
        kwargs["location"] = settings.PRIVATE_MEDIA_ROOT

        # This setting is explicitly `None` as the Azure File Storage filesystem
        # belongs to `root` user, otherwise will throw `PermissionError` on file uploads
        kwargs["file_permissions_mode"] = None

        super().__init__(*args, **kwargs)
