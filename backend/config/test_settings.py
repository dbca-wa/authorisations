"""Django settings overrides for automated test runs.

Pytest uses this module so local and CI test execution does not depend on a
PostgreSQL role with database-creation privileges. Keep overrides focused on
test speed, determinism, and isolation.
"""

from .settings import *  # noqa: F403


# Use in-memory SQLite for all tests — per-process isolation with no file artifacts.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
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

# Force django-vite into dev-mode during tests so template rendering does not
# require a built frontend manifest in CI backend-only jobs.
DJANGO_VITE["default"]["dev_mode"] = True  # noqa: F405
DJANGO_VITE["default"]["manifest_path"] = None  # noqa: F405