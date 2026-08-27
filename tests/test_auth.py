"""Authentication tests: login, token validation, protected endpoints.

Rewritten from a manual script that hit a live server on 127.0.0.1:8000. In CI
nothing listened there, so every request raised, each function swallowed the
error and returned False, and pytest reported them as passing because a
non-None return counts as a pass. Two functions took a `token` argument with no
fixture behind it and errored during collection.

These now run in-process against FastAPI's TestClient (see conftest.py) and
assert, so a failure is an actual failure.
"""

import pytest

from app.auth.dependencies import DEMO_MODE


def test_health_check(client):
    """The API reports healthy."""
    response = client.get("/health")
    assert response.status_code == 200


def test_login(client, credentials):
    """Valid credentials return a bearer token."""
    response = client.post("/token", data=credentials)
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload.get("access_token"), "no access_token in response"
    assert payload.get("token_type", "").lower() == "bearer"


def test_invalid_login(client):
    """Wrong credentials are rejected, and never return a token."""
    response = client.post(
        "/token",
        data={"username": "definitely-not-a-user", "password": "wrong-password"},
    )
    assert response.status_code in (400, 401), response.text
    assert "access_token" not in response.json()


def test_protected_endpoint(client, auth_headers):
    """A valid token grants access to a protected route."""
    response = client.get("/inventory/", headers=auth_headers)
    assert response.status_code == 200, response.text


def test_protected_endpoint_no_auth(client):
    """Unauthenticated access follows the configured demo posture.

    DEMO_MODE is deliberately enabled so the public portfolio deployment is
    usable without a login, and `get_current_user` then returns a stub user
    instead of raising. This asserts whichever behaviour is configured, so
    turning DEMO_MODE off makes the test enforce real authentication rather
    than quietly start failing.
    """
    response = client.get("/inventory/")
    if DEMO_MODE:
        assert response.status_code == 200, response.text
    else:
        assert response.status_code in (401, 403), response.text


def test_invalid_token(client):
    """A malformed token is refused unless the demo bypass is enabled."""
    response = client.get(
        "/inventory/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    if DEMO_MODE:
        assert response.status_code == 200, response.text
    else:
        assert response.status_code in (401, 403), response.text


@pytest.mark.parametrize("path", ["/agent/status", "/inventory/"])
def test_agent_endpoints(client, auth_headers, path):
    """Authenticated agent/inventory routes respond without a server error."""
    response = client.get(path, headers=auth_headers)
    assert response.status_code < 500, f"{path} -> {response.status_code}"
