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

# Django's test static handler serves files from STATICFILES_DIRS/finders.
# Include the collected static directory so Vite bundles are resolvable in E2E.
_TEST_STATIC_DIR = BASE_DIR / "static"  # noqa: F405
if _TEST_STATIC_DIR.exists() and _TEST_STATIC_DIR not in STATICFILES_DIRS:  # noqa: F405
    STATICFILES_DIRS.append(_TEST_STATIC_DIR)  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# For E2E tests with pytest-django live_server, disable session-based CSRF protection
# because session state cannot be safely shared between the test thread and live_server thread.
# Instead use token-based CSRF which does not require cross-thread session access.
CSRF_USE_SESSIONS = False

# Prefer bundled frontend assets in tests so browser E2E runs do not depend on
# a live Vite dev server. Fall back to dev mode only when a manifest is absent.
_TEST_MANIFEST_PATH = BASE_DIR / "static" / "manifest.json"  # noqa: F405
_RESOLVED_TEST_MANIFEST = (
    _TEST_MANIFEST_PATH
    if _TEST_MANIFEST_PATH.exists()
    else DJANGO_VITE["default"].get("manifest_path")  # noqa: F405
)

DJANGO_VITE = {
    "default": {
        **DJANGO_VITE["default"],  # noqa: F405
        "dev_mode": _RESOLVED_TEST_MANIFEST is None,
        "manifest_path": _RESOLVED_TEST_MANIFEST,
    }
}