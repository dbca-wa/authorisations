"""Pytest configuration for E2E tests.

This module keeps E2E tests self-contained by using an in-memory SQLite
database, running migrations, and loading local fixture data at test startup.
"""

from pathlib import Path
import base64
import io
import json
import os
import re
from typing import Callable

import pytest
from applications.models import Application
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from users.models import User


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
    """Run migrations once for E2E execution against the in-memory database."""
    with django_db_blocker.unblock():
        # Ensure schema exists even when E2E is run in isolation.
        call_command("migrate", verbosity=0, run_syncdb=True)


@pytest.fixture(autouse=True)
def load_e2e_seed_data(db):
    """Load deterministic seed data before each E2E test after DB resets."""
    fixture_path = Path(__file__).parent / "fixtures" / "e2e_seed.json"
    call_command("loaddata", str(fixture_path), verbosity=0)


@pytest.fixture(scope="session", autouse=True)
def configure_vite_for_e2e(django_db_setup):
    """Use static built assets for browser E2E so no Vite dev server is required."""
    manifest_path = Path(settings.BASE_DIR) / "static" / "manifest.json"
    settings.DJANGO_VITE["default"]["dev_mode"] = False
    settings.DJANGO_VITE["default"]["manifest_path"] = str(manifest_path)


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


def _get_session_cookie_value(client, user: User) -> str:
    """Return the authenticated Django session cookie value for a user."""
    client.force_login(user)
    cookie_name = settings.SESSION_COOKIE_NAME
    return str(client.cookies[cookie_name].value)


def _extract_client_config(response_text: str) -> dict[str, str]:
    """Decode backend-provided client config from the SPA shell HTML payload."""
    match = re.search(r'<script id="config" type="application/json">(.*?)</script>', response_text, flags=re.DOTALL)
    if not match:
        raise AssertionError("Failed to find client config in response HTML.")

    encoded_json = json.loads(match.group(1))
    decoded = base64.b64decode(encoded_json).decode("utf-8")
    return json.loads(decoded)


@pytest.fixture
def e2e_users(db):
    """Expose deterministic seed users for E2E role-based scenarios."""
    return {
        "applicant": User.objects.get(username="e2e-applicant"),
        "reviewer": User.objects.get(username="e2e-reviewer"),
        "other": User.objects.get(username="e2e-other-applicant"),
    }


@pytest.fixture
def authenticated_request_context_factory(playwright, live_server, client):
    """Create request contexts authenticated as a chosen user with CSRF headers ready."""
    def _factory(user: User):
        session_cookie = _get_session_cookie_value(client, user)
        cookie_header = f"{settings.SESSION_COOKIE_NAME}={session_cookie}"
        request_context = playwright.request.new_context(
            base_url=live_server.url,
            extra_http_headers={"Cookie": cookie_header},
        )

        response = request_context.get("/my-applications")
        assert response.status == 200
        client_config = _extract_client_config(response.text())

        return {
            "context": request_context,
            "csrf_header": client_config["csrf_header"],
            "csrf_token": client_config["csrf_token"],
        }

    return _factory


@pytest.fixture
def authenticated_browser_context_factory(browser, live_server, client):
    """Create browser contexts authenticated as a chosen user for SPA interactions."""
    def _factory(user: User):
        session_cookie = _get_session_cookie_value(client, user)
        context = browser.new_context(base_url=live_server.url)
        context.add_cookies([
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie,
                "url": live_server.url,
                "httpOnly": True,
            }
        ])
        return context

    return _factory


@pytest.fixture(autouse=True)
def bypass_turnstile_verification(monkeypatch):
    """Bypass external Turnstile verification for deterministic local E2E runs."""
    monkeypatch.setattr("applications.serialisers.verify_turnstile_token", lambda *args, **kwargs: True)


@pytest.fixture(autouse=True)
def bypass_prince_pdf_generation(monkeypatch):
    """Avoid Prince runtime dependency by returning deterministic PDF bytes in E2E."""
    def _fake_generate_pdf(self, request=None):
        return io.BytesIO(b"%PDF-1.4\n%E2E\n")

    monkeypatch.setattr(Application, "generate_pdf", _fake_generate_pdf)


@pytest.fixture
def mock_turnstile_script():
    """Provide a helper that mocks Cloudflare Turnstile script loading on a page."""
    def _attach(page):
        page.route(
            "https://challenges.cloudflare.com/turnstile/v0/api.js*",
            lambda route: route.fulfill(
                status=200,
                content_type="application/javascript",
                body=(
                    "window.turnstile={"
                    "render:function(container,opts){"
                    "if(opts&&typeof opts.callback==='function'){opts.callback('e2e-turnstile-token');}"
                    "return 'widget-e2e';"
                    "},"
                    "execute:function(){},"
                    "reset:function(){},"
                    "remove:function(){},"
                    "getResponse:function(){return 'e2e-turnstile-token';},"
                    "isExpired:function(){return false;}"
                    "};"
                ),
            ),
        )

    return _attach
