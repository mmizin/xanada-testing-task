"""Session-scoped fixture for the authentication feature's login API client.

Lives under the authentication feature package (not ``src/fixtures``) because
``LoginApiClient`` is feature-specific and has no meaning outside this suite.
"""

from __future__ import annotations

import pytest

from src.features.authentication.api.login_client import LoginApiClient
from src.infra.api.http_client import ApiHttpClient


@pytest.fixture()
def login_client(http_client: ApiHttpClient) -> LoginApiClient:
    return LoginApiClient(http_client)