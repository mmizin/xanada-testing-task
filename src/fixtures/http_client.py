"""Session-scoped fixture for the shared transport-level HTTP client.

Lives under ``src/fixtures`` (not a feature package) because ``ApiHttpClient``
is infra-level and reusable across any future feature suite, not just
authentication.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.infra.api.http_client import ApiHttpClient
from src.infra.config import Settings


@pytest.fixture()
def http_client(settings: Settings) -> Iterator[ApiHttpClient]:
    with ApiHttpClient(base_url=settings.base_url) as client:
        yield client