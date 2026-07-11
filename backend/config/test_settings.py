"""Django settings overrides for automated test runs.

Pytest uses this module so local and CI test execution does not depend on a
PostgreSQL role with database-creation privileges. Keep overrides focused on
test speed, determinism, and isolation.
"""

from pathlib import Path

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
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Keep django-vite in dev-mode by default for backend-only test jobs, while
# allowing E2E jobs to force static/manifest mode via environment variables.
DJANGO_VITE_TEST_DEV_MODE = env("DJANGO_VITE_TEST_DEV_MODE", cast=bool, default=True)  # noqa: F405
DJANGO_VITE_TEST_MANIFEST_PATH = env("DJANGO_VITE_TEST_MANIFEST_PATH", default=None)  # noqa: F405

DJANGO_VITE["default"]["dev_mode"] = DJANGO_VITE_TEST_DEV_MODE  # noqa: F405
if DJANGO_VITE_TEST_MANIFEST_PATH:
    manifest_path = Path(DJANGO_VITE_TEST_MANIFEST_PATH)
    if not manifest_path.is_absolute():
        manifest_path = BASE_DIR / manifest_path  # noqa: F405
    DJANGO_VITE["default"]["manifest_path"] = str(manifest_path)  # noqa: F405
elif DJANGO_VITE_TEST_DEV_MODE:
    DJANGO_VITE["default"]["manifest_path"] = None  # noqa: F405
else:
    DJANGO_VITE["default"]["manifest_path"] = str(BASE_DIR / "static" / "manifest.json")  # noqa: F405