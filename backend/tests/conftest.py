"""
tests/conftest.py — Shared pytest fixtures.

No GEMINI_API_KEY is required for any test in this suite.
The Gemini client is never instantiated during unit or health tests.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure no real API key is accidentally loaded during tests.
# Tests that require mocked AI responses will set their own env vars.
os.environ.setdefault("GEMINI_MODEL", "gemini-2.5-flash")
os.environ.setdefault("GEMINI_API_KEY", "")  # Explicitly empty — never a real key


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient shared across the session."""
    # Import after env vars are set so Settings picks them up.
    from app.config import get_settings
    get_settings.cache_clear()          # Ensure fresh settings with test env vars

    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def client_no_model():
    """TestClient with GEMINI_MODEL explicitly unset (empty string)."""
    original = os.environ.pop("GEMINI_MODEL", None)
    os.environ["GEMINI_MODEL"] = ""

    from app.config import get_settings
    get_settings.cache_clear()

    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    # Restore
    if original is not None:
        os.environ["GEMINI_MODEL"] = original
    else:
        os.environ.pop("GEMINI_MODEL", None)
    get_settings.cache_clear()
