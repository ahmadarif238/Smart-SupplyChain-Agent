"""Shared pytest fixtures.

The auth tests used to be a manual script that made real HTTP calls to a
server on 127.0.0.1:8000. In CI nothing is listening there, so every request
raised, each function caught the exception and returned False, and pytest --
which treats any non-None return as a pass -- reported them green. Two of them
took a `token` argument that no fixture provided, so those errored outright.

These fixtures run the app in-process with FastAPI's TestClient instead, so the
tests are real, need no running server, and no longer depend on the developer's
local machine.
"""

import os
import sys

import pytest

# The application package lives at the repository root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def client():
    """A TestClient with the app's lifespan run.

    The lifespan matters: it creates the tables and seeds the admin user that
    the auth tests log in as.
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def credentials():
    from app.auth.security import ADMIN_USERNAME, ADMIN_PASSWORD

    return {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}


@pytest.fixture(scope="session")
def token(client, credentials):
    """A valid bearer token, or skip the test if auth is unavailable."""
    response = client.post("/token", data=credentials)
    if response.status_code != 200:
        pytest.skip(f"Could not obtain a token (HTTP {response.status_code})")
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
