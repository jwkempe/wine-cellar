import os

# Set before any app module is imported: ai.py builds its client and main.py
# reads config at import time. Values are dummies — tests never hit the
# network or the database.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("CLERK_JWKS_URL", "https://example.test/jwks")

import pytest
from fastapi.testclient import TestClient

import main
from auth import get_current_user

TEST_USER = "user_test"


@pytest.fixture
def client(monkeypatch):
    """TestClient authenticated as TEST_USER, with startup DB init stubbed."""
    monkeypatch.setattr(main, "init_db", lambda: None)
    main.app.dependency_overrides[get_current_user] = lambda: TEST_USER
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture
def anon_client(monkeypatch):
    """TestClient with no auth override — requests arrive unauthenticated."""
    monkeypatch.setattr(main, "init_db", lambda: None)
    with TestClient(main.app) as c:
        yield c
