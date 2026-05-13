"""Django settings overrides for automated test runs.

Pytest uses this module so local and CI test execution does not depend on a
PostgreSQL role with database-creation privileges. Keep overrides focused on
test speed, determinism, and isolation.
"""

from .settings import *  # noqa: F403


# Use a file-backed SQLite database so pytest-django can create isolated test
# databases without requiring CREATEDB privileges on PostgreSQL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}

# Speed up authentication-heavy tests without affecting production hashing.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Keep uploaded test files local and disposable.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": BASE_DIR / "test-media",  # noqa: F405
        },
    },
    "staticfiles": STORAGES["staticfiles"],  # noqa: F405
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"