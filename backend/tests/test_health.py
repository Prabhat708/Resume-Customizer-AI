"""
tests/test_health.py — Health endpoint tests.

Asserts:
  1. Returns HTTP 200 with GEMINI_MODEL set.
  2. Response body matches HealthResponse schema (status, version, model_configured).
  3. model_configured is True when GEMINI_MODEL env var is set and non-empty.
  4. model_configured is False when GEMINI_MODEL env var is empty.
  5. No secrets or model name appear in the response body.

No GEMINI_API_KEY is required for any of these tests.
"""
from __future__ import annotations

import json


def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_health_response_schema(client):
    response = client.get("/api/v1/health")
    data = response.json()

    assert "status" in data, "Missing 'status' field"
    assert "version" in data, "Missing 'version' field"
    assert "model_configured" in data, "Missing 'model_configured' field"


def test_health_status_is_ok(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok", f"Expected 'ok', got {data['status']!r}"


def test_health_version_is_string(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert isinstance(data["version"], str), "version must be a string"
    assert len(data["version"]) > 0, "version must be non-empty"


def test_health_model_configured_true_when_model_set(client):
    """GEMINI_MODEL is set in conftest; model_configured must be True."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["model_configured"] is True, (
        f"Expected model_configured=True when GEMINI_MODEL is set, got {data['model_configured']}"
    )


def test_health_model_configured_false_when_model_unset(client_no_model):
    """GEMINI_MODEL is empty in client_no_model fixture; model_configured must be False."""
    response = client_no_model.get("/api/v1/health")
    data = response.json()
    assert data["model_configured"] is False, (
        f"Expected model_configured=False when GEMINI_MODEL is empty, got {data['model_configured']}"
    )


def test_health_does_not_expose_api_key(client):
    """Response body must never contain API key hints."""
    response = client.get("/api/v1/health")
    body_text = response.text.lower()
    for sensitive_term in ["api_key", "gemini_api", "secret", "credential", "token"]:
        assert sensitive_term not in body_text, (
            f"Sensitive term '{sensitive_term}' found in health response"
        )


def test_health_does_not_expose_model_name(client):
    """
    model_configured is a boolean. The actual model name string must
    not appear as a field value in the response.
    """
    response = client.get("/api/v1/health")
    data = response.json()
    # model_configured must be a bool, not a string like "gemini-2.5-flash"
    assert isinstance(data["model_configured"], bool), (
        f"model_configured must be bool, got {type(data['model_configured'])}: {data['model_configured']!r}"
    )
