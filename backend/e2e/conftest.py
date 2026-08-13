"""Pytest configuration for E2E tests.

This module keeps E2E tests self-contained by using an in-memory SQLite
database, running migrations, and loading local fixture data at test startup.
"""

from pathlib import Path
import base64
from datetime import UTC, datetime
import io
import json
import os
import re
import shutil
from typing import Callable

import pytest
from applications.models import Application
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from questionnaires.models import Questionnaire
from users.models import User


# Playwright's sync runner may keep an event loop active in the test thread.
# Allow controlled sync DB access for pytest-django lifecycle hooks.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

# Ensure Turnstile site key is available for E2E tests - required for frontend to load Turnstile script
os.environ.setdefault("TURNSTILE_SITE_KEY", "0x0000000000000000_e2e_test_key")


def _timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for debug events."""
    return datetime.now(UTC).isoformat()


def _append_capped(buffer: list[dict[str, str]], payload: dict[str, str], *, max_items: int = 500):
    """Append to a debug buffer while keeping its size bounded."""
    if len(buffer) >= max_items:
        return
    buffer.append(payload)


def _as_error_text(failure) -> str:
    """Normalise Playwright request failure payloads to text."""
    if isinstance(failure, dict):
        return str(failure.get("errorText", ""))
    if failure is None:
        return ""
    return str(failure)


def _ensure_page_debug_store(request, page):
    """Return the mutable debug store for a page on the current test node."""
    store = getattr(request.node, "_e2e_page_debug", {})
    key = str(id(page))
    if key not in store:
        store[key] = {
            "console": [],
            "page_errors": [],
            "request_failures": [],
            "http_errors": [],
        }
    setattr(request.node, "_e2e_page_debug", store)
    return key, store[key]


def _attach_page_debug_listeners(request, page):
    """Attach console/page/network debug listeners for per-page diagnostics."""
    _, page_debug = _ensure_page_debug_store(request, page)

    def _on_console(message):
        message_type = message.type
        if message_type not in {"error", "warning"}:
            return
        location = message.location or {}
        _append_capped(
            page_debug["console"],
            {
                "timestamp": _timestamp(),
                "type": message_type,
                "text": message.text,
                "url": str(location.get("url", "")),
                "line": str(location.get("lineNumber", "")),
                "column": str(location.get("columnNumber", "")),
            },
        )

    def _on_page_error(error):
        _append_capped(
            page_debug["page_errors"],
            {
                "timestamp": _timestamp(),
                "message": str(error),
            },
        )

    def _on_request_failed(request_obj):
        _append_capped(
            page_debug["request_failures"],
            {
                "timestamp": _timestamp(),
                "url": request_obj.url,
                "method": request_obj.method,
                "resource_type": request_obj.resource_type,
                "error_text": _as_error_text(request_obj.failure),
            },
        )

    def _on_response(response):
        status_code = response.status
        if status_code < 400:
            return
        req = response.request
        _append_capped(
            page_debug["http_errors"],
            {
                "timestamp": _timestamp(),
                "url": response.url,
                "status": str(status_code),
                "method": req.method,
                "resource_type": req.resource_type,
            },
        )

    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)
    page.on("requestfailed", _on_request_failed)
    page.on("response", _on_response)


def _capture_failed_page(page, page_prefix: str, nodeid: str, page_debug: dict, artefacts_dir: Path, log_file):
    """Capture screenshot, HTML, debug JSON, and video for a failed page."""
    screenshot_path = artefacts_dir / f"{page_prefix}.png"
    html_path = artefacts_dir / f"{page_prefix}.html"
    debug_path = artefacts_dir / f"{page_prefix}-debug.json"

    debug_payload = {
        "nodeid": nodeid,
        "captured_at": _timestamp(),
        "page_url": page.url,
        "page_title": page.title(),
        "console": page_debug.get("console", []),
        "page_errors": page_debug.get("page_errors", []),
        "request_failures": page_debug.get("request_failures", []),
        "http_errors": page_debug.get("http_errors", []),
    }
    debug_path.write_text(json.dumps(debug_payload, indent=2), encoding="utf-8")

    page.screenshot(path=str(screenshot_path), full_page=True)
    html_path.write_text(page.content(), encoding="utf-8")
    # Close the page so Playwright finalises any video file.
    page.close()
    log_file.write(f"Captured {screenshot_path.name}, {html_path.name}, and {debug_path.name}\n")

    if page.video:
        video_path = Path(page.video.path())
        if video_path.exists():
            copied_video_path = artefacts_dir / f"{page_prefix}{video_path.suffix or '.webm'}"
            shutil.copy(video_path, copied_video_path)
            log_file.write(f"Copied video {copied_video_path.name}\n")


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

    # pytest-django live_server wraps the app with StaticFilesHandler, which serves
    # static files via finder paths rather than WhiteNoise's STATIC_ROOT lookup.
    # In static mode we therefore expose STATIC_ROOT to finders so post-processed
    # fingerprinted assets (for example main-<hash>.<fingerprint>.css) resolve.
    static_root = Path(settings.STATIC_ROOT)
    if static_root.exists():
        static_dirs = list(settings.STATICFILES_DIRS)
        if static_root not in static_dirs:
            settings.STATICFILES_DIRS = [*static_dirs, static_root]


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
        "applicant": User.objects.get(username="e2e-applicant@example.com"),
        "reviewer": User.objects.get(username="e2e-reviewer@example.com"),
        "other": User.objects.get(username="e2e-other@example.com"),
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
def authenticated_browser_context_factory(browser, live_server, client, request):
    """Create browser contexts authenticated as a chosen user for SPA interactions."""
    def _factory(user: User):
        session_cookie = _get_session_cookie_value(client, user)
        video_dir = Path(settings.BASE_DIR) / "test-results" / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        context = browser.new_context(
            base_url=live_server.url,
            record_video_dir=str(video_dir),
        )
        context.add_cookies([
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie,
                "url": live_server.url,
                "httpOnly": True,
            }
        ])

        def _on_new_page(page):
            _attach_page_debug_listeners(request, page)

        context.on("page", _on_new_page)

        # Register listeners for pages that may already exist on the context.
        for existing_page in context.pages:
            _attach_page_debug_listeners(request, existing_page)

        # Tests in this suite often use custom contexts/pages instead of the
        # built-in pytest-playwright page fixture, so track contexts to allow
        # forced failure artefact capture in pytest hooks.
        tracked_contexts = getattr(request.node, "_e2e_browser_contexts", [])
        tracked_contexts.append(context)
        setattr(request.node, "_e2e_browser_contexts", tracked_contexts)
        return context

    return _factory


def _failure_artifacts_dir(nodeid: str) -> Path:
    """Return a deterministic per-test artefact directory under test-results."""
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", nodeid)
    target_dir = Path(settings.BASE_DIR) / "test-results" / "forced-failures" / safe_id
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshots/HTML when browser E2E tests fail.

    This guarantees diagnostically useful artefacts for failures involving
    custom contexts/pages, which pytest-playwright does not always capture.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    contexts = getattr(item, "_e2e_browser_contexts", [])
    if not contexts:
        return

    page_debug_store = getattr(item, "_e2e_page_debug", {})

    artefacts_dir = _failure_artifacts_dir(item.nodeid)
    capture_log = artefacts_dir / "capture.log"

    with capture_log.open("w", encoding="utf-8") as log_file:
        for context_index, context in enumerate(contexts):
            for page_index, page in enumerate(context.pages):
                page_prefix = f"context-{context_index}-page-{page_index}"

                try:
                    if not page.is_closed():
                        page_debug = page_debug_store.get(str(id(page)), {})
                        _capture_failed_page(
                            page=page,
                            page_prefix=page_prefix,
                            nodeid=item.nodeid,
                            page_debug=page_debug,
                            artefacts_dir=artefacts_dir,
                            log_file=log_file,
                        )
                    else:
                        log_file.write(f"Skipped closed page: {page_prefix}\n")
                except Exception as exc:  # pragma: no cover - best-effort diagnostics
                    log_file.write(f"Failed capture for {page_prefix}: {exc}\n")


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
                    "console.log('MOCK TURNSTILE RENDER CALLED');"
                    "if(opts&&typeof opts.callback==='function'){"
                    "console.log('MOCK TURNSTILE CALLBACK INVOKED');"
                    "opts.callback('e2e-turnstile-token');"
                    "}"
                    "return 'widget-e2e';"
                    "},"
                    "execute:function(){},"
                    "reset:function(){},"
                    "remove:function(){},"
                    "getResponse:function(){return 'e2e-turnstile-token';},"
                    "isExpired:function(){return false;}"
                    "};"
                    "console.log('MOCK TURNSTILE SCRIPT LOADED');"
                ),
            ),
        )

    return _attach


@pytest.fixture
def draft_application(authenticated_request_context_factory, e2e_users):
    """Create a draft application via API and return its key."""
    applicant = e2e_users["applicant"]
    auth_context = authenticated_request_context_factory(applicant)
    questionnaire = Questionnaire.objects.select_related("process").get(
        process__slug="aec", code="new-application", version=1
    )
    request_context = auth_context["context"]

    try:
        response = request_context.post(
            "/api/applications",
            data=json.dumps({
                "process_slug": questionnaire.process.slug,
                "questionnaire_id": questionnaire.id,
                "questionnaire_code": questionnaire.code,
                "questionnaire_version": questionnaire.version,
                "collection_notice_agreed": True,
                "turnstile_token": "e2e-turnstile-token",
            }),
            headers={
                str(auth_context["csrf_header"]): str(auth_context["csrf_token"]),
                "Content-Type": "application/json",
            },
        )
        assert response.status == 201
        app_key = response.json()["key"]
    finally:
        request_context.dispose()

    return applicant, app_key
