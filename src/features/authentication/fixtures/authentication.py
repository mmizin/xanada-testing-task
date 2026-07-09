"""Fixtures for the authentication feature's API client.

Lives under the authentication feature package (not ``src/fixtures``) because
``AuthenticationApiClient`` is feature-specific and has no meaning outside
this suite.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.infra.api.http_client import ApiHttpClient


@pytest.fixture()
def auth_client(http_client: ApiHttpClient) -> AuthenticationApiClient:
    return AuthenticationApiClient(http_client)


@pytest.fixture()
def anonymous_auth_client(
    http_client_factory: Callable[[], ApiHttpClient],
) -> Iterator[AuthenticationApiClient]:
    """A fresh ``AuthenticationApiClient`` with its own httpx.Client/cookie jar.

    Never use ``auth_client`` for an unauthenticated/negative-control request
    after a login on that same client: httpx.Client persists cookies set by
    the server across every subsequent request on that instance, so a call
    with no explicit ``session-token`` header could still authenticate via a
    leaked cookie (see ``ApiHttpClient``'s docstring). This fixture is a
    separate instance — guaranteed no prior auth state — for exactly that
    case (TC-003's control assertion). Built via ``http_client_factory`` so
    it still shares the suite's rate limiter (ADR-004).
    """
    with http_client_factory() as client:
        yield AuthenticationApiClient(client)
