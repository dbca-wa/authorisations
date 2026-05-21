"""Pytest configuration for E2E tests.

This module keeps E2E tests self-contained by using an in-memory SQLite
database, running migrations, and loading local fixture data at test startup.
"""

from pathlib import Path
import os
from typing import Callable

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper


# Playwright's sync runner may keep an event loop active in the test thread.
# Allow controlled sync DB access for pytest-django lifecycle hooks.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    """Configure E2E tests to use an in-memory SQLite database.

    A shared-cache SQLite URI is used so Django test-server connections can
    see the same in-memory database during E2E execution.
    """
    in_memory_name = "file:e2e_shared?mode=memory&cache=shared"

    # Preserve existing DB keys (for example ATOMIC_REQUESTS) and only replace
    # the engine/name knobs needed for E2E isolation.
    current_default = settings.DATABASES.get("default", {}).copy()
    current_test = current_default.get("TEST", {}).copy()

    current_default.update(
        {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": in_memory_name,
            "OPTIONS": {"uri": True, "check_same_thread": False},
            "TEST": {
                **current_test,
                "NAME": in_memory_name,
                "MIRROR": None,
                "DEPENDENCIES": [],
            },
        }
    )

    settings.DATABASES["default"] = current_default


@pytest.fixture(scope="session", autouse=True)
def prepare_e2e_database(django_db_setup, django_db_blocker):
    """Run migrations and load local seed fixtures for every E2E run."""
    fixture_path = Path(__file__).parent / "fixtures" / "e2e_seed.json"

    with django_db_blocker.unblock():
        # Ensure schema exists even when E2E is run in isolation.
        call_command("migrate", verbosity=0, run_syncdb=True)
        # Load deterministic baseline data from local filesystem fixtures.
        call_command("loaddata", str(fixture_path), verbosity=0)


@pytest.fixture(scope="session", autouse=True)
def allow_e2e_db_thread_sharing(django_db_setup, django_db_blocker):
    """Permit DB connection sharing across live_server threads during E2E.

    Django's live test server handles requests in worker threads; enabling
    thread sharing avoids teardown warnings with in-memory SQLite.
    """
    with django_db_blocker.unblock():
        connection = connections["default"]
        connection.inc_thread_sharing()

    yield

    with django_db_blocker.unblock():
        connection.dec_thread_sharing()


@pytest.fixture(scope="session", autouse=True)
def relax_sqlite_thread_validation_for_e2e():
    """Relax SQLite thread validation during E2E live_server runs.

    Django's threaded live_server can close DB connections from a different
    thread than where they were created, which raises benign teardown warnings
    for SQLite in-memory E2E runs. Restrict this relaxation to E2E only.
    """
    original_validate: Callable[..., None] = BaseDatabaseWrapper.validate_thread_sharing

    def _ignore_thread_sharing(self):
        return None

    BaseDatabaseWrapper.validate_thread_sharing = _ignore_thread_sharing
    try:
        yield
    finally:
        BaseDatabaseWrapper.validate_thread_sharing = original_validate
