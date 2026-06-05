"""
Shared pytest fixtures for AI Security Lab.

Each test gets an isolated app backed by a temporary SQLite database, so tests
never touch the developer's real database and never depend on each other.
"""
import os

os.environ.setdefault('FLASK_ENV', 'testing')

import pytest

from app import create_app
from config import TestingConfig
from utils.rate_limiter import reset_limits


@pytest.fixture
def app(tmp_path):
    """Create a fresh Flask app with an isolated temp database."""
    class _TestConfig(TestingConfig):
        TESTING = True
        SECRET_KEY = 'test-secret'
        DATABASE_PATH = tmp_path / 'test.db'
        MODEL_CACHE_DIR = tmp_path / 'cache'
        WTF_CSRF_ENABLED = False
        RATE_LIMIT_ENABLED = False

    application = create_app(_TestConfig)
    reset_limits()
    yield application
    reset_limits()


@pytest.fixture
def client(app):
    """A test client. GET / once to establish a session with a session_id."""
    c = app.test_client()
    c.get('/')  # triggers main blueprint before_request -> sets session_id
    return c
