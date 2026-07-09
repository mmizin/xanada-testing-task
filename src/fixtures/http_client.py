"""Function-scoped fixtures for the shared transport-level HTTP client.

Lives under ``src/fixtures`` (not a feature package) because ``ApiHttpClient``
is infra-level and reusable across any future feature suite, not just
authentication.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from src.infra.api.http_client import ApiHttpClient
from src.infra.config import Settings
from src.infra.rate_limiter import CrossProcessRateLimiter, as_request_hook


@pytest.fixture()
def http_client_factory(
    settings: Settings, rate_limiter: CrossProcessRateLimiter | None
) -> Callable[[], ApiHttpClient]:
    """Build fresh, rate-limited ``ApiHttpClient`` instances (ADR-004).

    The sanctioned way to get an extra isolated client (own cookie jar)
    within a test — never construct ``ApiHttpClient`` directly, or it skips
    the shared rate limiter. Only the ``request`` hook key is set; httpx
    defaults ``response`` to ``[]`` on its own, so this doesn't clobber a
    response hook added here later.
    """

    def _build() -> ApiHttpClient:
        return ApiHttpClient(
            base_url=settings.base_url,
            event_hooks={"request": as_request_hook(rate_limiter)},
        )

    return _build


@pytest.fixture()
def http_client(http_client_factory: Callable[[], ApiHttpClient]) -> Iterator[ApiHttpClient]:
    with http_client_factory() as client:
        yield client
