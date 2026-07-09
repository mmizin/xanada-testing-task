"""Root pytest fixtures: composition root for configuration and clients.

Per Architecture Design §7/§8: configuration is validated via these fixtures
before any test runs — a missing/invalid env var fails fast instead of
surfacing as a confusing failure deep inside a test.
"""

from __future__ import annotations

import dataclasses
import json

import pytest
from filelock import FileLock

from src.infra.config import Settings
from src.infra.rate_limiter import CrossProcessRateLimiter

# Feature/infra fixture modules registered as plugins so their fixtures
# (http_client, auth_client) are discoverable across the whole test session,
# even though they live outside the tests/ tree that pytest walks for conftest.py.
pytest_plugins = [
    "src.fixtures.http_client",
    "src.features.authentication.fixtures.authentication",
]


@pytest.fixture(scope="session")
def settings(tmp_path_factory: pytest.TempPathFactory, worker_id: str) -> Settings:
    """Load env-driven config exactly once per test run, even under xdist.

    Session scope alone only guarantees "once per worker process" (each
    xdist worker runs its own session) — see the pytest-xdist how-to,
    "Making session-scoped fixtures execute only once". Since Settings.load()
    is deterministic (same env -> same result) and cheap, the single-process
    ("master") case just loads it directly; under xdist, the first worker to
    grab the lock loads and caches it to a shared temp file, and every other
    worker reads that cached JSON instead of re-parsing the environment.
    """
    if worker_id == "master":
        return Settings.load()

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    cache_file = root_tmp_dir / "settings.json"
    with FileLock(str(cache_file) + ".lock"):
        if cache_file.is_file():
            data = json.loads(cache_file.read_text())
        else:
            data = dataclasses.asdict(Settings.load())
            cache_file.write_text(json.dumps(data))
    return Settings(**data)


@pytest.fixture(scope="session")
def rate_limiter(settings: Settings) -> CrossProcessRateLimiter | None:
    """The shared limiter instance (ADR-004), or ``None`` when disabled.

    Session-scoped for cheapness only — coordination itself lives in the
    on-disk state file, not in this object, so a fresh instance per test
    would behave identically.
    """
    if not settings.rate_limit_enabled:
        return None
    return CrossProcessRateLimiter(
        key=settings.base_url,
        max_per_minute=settings.rate_limit_max_per_minute,
    )
