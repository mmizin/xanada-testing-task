"""TC-024: Login establishes a session cookie usable for cookie-based authentication.

See test-cases/api/authentication/login.md#tc-024 for the full case spec.
Split out of TC-003, which covers header-based auth only.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.infra.config import Settings


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Session validity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Login establishes a session cookie usable for cookie-based authentication")
@allure.testcase("TC-024")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "auth")
@pytest.mark.positive
@pytest.mark.login
@pytest.mark.integration
def test_login_establishes_session_cookie(
    settings: Settings, auth_client: AuthenticationApiClient
) -> None:
    with allure.step("Log in with the configured real account credentials"):
        login_response = auth_client.login(settings.username, settings.password)
        assert (
            login_response.status_code == 200
        ), f"expected 200, got {login_response.status_code}: {login_response.raw.text}"

    with allure.step("Assert the login response itself sets a session-token cookie"):
        # Per docs: token can be sent as cookie or header (documented contract).
        assert "session-token" in login_response.cookie_names, (
            "expected the login response to Set-Cookie a session-token, "
            f"got: {login_response.cookie_names}"
        )
        assert "session-token" in auth_client.http_client.cookie_names, (
            "expected the client's cookie jar to pick up the session-token "
            f"cookie; jar had: {auth_client.http_client.cookie_names}"
        )

    with allure.step("Assert the cookie alone authenticates a session-status check"):
        # No token passed: call rides on stored cookie, proving documented cookie-based auth works.
        cookie_authenticated_response = auth_client.get_session()
        allure.attach(
            str(cookie_authenticated_response),
            name="Cookie-authenticated response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert cookie_authenticated_response.status_code == 200, (
            "cookie-based auth failed: expected 200, got "
            f"{cookie_authenticated_response.status_code}: {cookie_authenticated_response.raw.text}"
        )