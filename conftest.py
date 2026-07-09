"""Root pytest fixtures: composition root for configuration and clients.

Per Architecture Design §7/§8: configuration is validated via these fixtures
before any test runs — a missing/invalid env var fails fast instead of
surfacing as a confusing failure deep inside a test.
"""

from __future__ import annotations

import pytest

from src.infra.config import Settings

# Feature/infra fixture modules registered as plugins so their fixtures
# (http_client, login_client) are discoverable across the whole test session,
# even though they live outside the tests/ tree that pytest walks for conftest.py.
pytest_plugins = [
    "src.fixtures.http_client",
    "src.features.authentication.fixtures.login_client",
]


@pytest.fixture()
def settings() -> Settings:
    return Settings.load()