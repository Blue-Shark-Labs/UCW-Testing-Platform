"""Shared fixtures for the Playwright browser tests.

The Flask app runs in a background thread with every database call mocked, so no
Postgres instance is needed. Run with: make test-e2e
"""

import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from playwright.sync_api import Error as PlaywrightError, sync_playwright
from werkzeug.serving import make_server

from rest.router import create_app

USER_ID = "11111111-1111-1111-1111-111111111111"
E2E_DIR = Path(__file__).parent


def _chromium_available():
    try:
        with sync_playwright() as playwright:
            playwright.chromium.launch().close()
        return True
    except PlaywrightError:
        return False


def pytest_collection_modifyitems(config, items):
    e2e_items = [item for item in items if E2E_DIR in item.path.parents]
    if e2e_items and not _chromium_available():
        skip = pytest.mark.skip(reason="Chromium isn't installed (run: make install-e2e)")
        for item in e2e_items:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def live_server():
    app = create_app()
    # The browser talks to the server over plain http.
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield SimpleNamespace(app=app, url=f"http://127.0.0.1:{server.server_port}")
    server.shutdown()


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server.url


@pytest.fixture(autouse=True)
def no_database():
    """Fails any query that isn't mocked, and stubs the per-request user lookup."""
    with patch("database.connection.psycopg.connect", side_effect=RuntimeError("e2e tests must not use the database")), \
            patch("rest.router.PostgresConnectionProvider") as router_provider:
        cursor = router_provider.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("Jane", "Doe", "student", False)
        yield


@pytest.fixture(autouse=True)
def block_external_requests(page):
    page.route("**/fonts.googleapis.com/**", lambda route: route.abort())
    page.route("**/fonts.gstatic.com/**", lambda route: route.abort())


@pytest.fixture
def sign_in(live_server, context):
    """Adds a signed session cookie to the browser, as if the user had logged in."""

    def _sign_in(role="student"):
        app = live_server.app
        serializer = app.session_interface.get_signing_serializer(app)
        context.add_cookies([{
            "name": app.config["SESSION_COOKIE_NAME"],
            "value": serializer.dumps({"user_id": USER_ID, "role": role}),
            "url": live_server.url,
        }])

    return _sign_in
