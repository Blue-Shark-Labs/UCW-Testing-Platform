import pytest

from rest.router import create_app


@pytest.fixture
def app():
    """Create a test Flask app shared across all REST route tests."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client from the shared Flask app."""
    return app.test_client()
