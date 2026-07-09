"""TC-003: Successful login grants access to authenticated resources.

See test-cases/api/authentication/login.md#tc-003 for the full case spec.
Cookie-specific behavior (Set-Cookie, cookie-based auth) is TC-024, not here.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.session import extract_session_token
from src.infra.config import Settings


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Session validity")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Successful login grants access to authenticated resources")
@allure.testcase("TC-003")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("smoke", "regression", "integration", "auth")
@pytest.mark.positive
@pytest.mark.login
@pytest.mark.integration
def test_login_grants_access_to_authenticated_resources(
    settings: Settings,
    auth_client: AuthenticationApiClient,
    anonymous_auth_client: AuthenticationApiClient,
) -> None:
    with allure.step("Log in to obtain a fresh session token"):
        login_response = auth_client.login(settings.username, settings.password)
        assert (
            login_response.status_code == 200
        ), f"expected 200, got {login_response.status_code}: {login_response.raw.text}"
        token = extract_session_token(login_response)
        assert token, f"expected a non-empty session-token to authenticate with: {login_response.raw.text}"

    with allure.step("Assert the token authenticates a session-status check"):
        authenticated_response = auth_client.get_session(token)
        allure.attach(
            str(authenticated_response),
            name="Authenticated response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert authenticated_response.status_code == 200, (
            f"token was rejected: expected 200, got {authenticated_response.status_code}: "
            f"{authenticated_response.raw.text}"
        )

    with allure.step("Control: an unauthenticated session is rejected"):
        # A fresh anonymous_auth_client is required here, not auth_client: httpx.Client
        # persists the Set-Cookie from the login above across every later request on
        # that same instance, so reusing auth_client would authenticate via the leaked
        # cookie and pass even if token-checking were broken (see TC-024).
        unauthenticated_response = anonymous_auth_client.get_session()
        allure.attach(
            str(unauthenticated_response),
            name="Unauthenticated response",
            attachment_type=allure.attachment_type.TEXT,
        )
        # Per the docs: "A 401 response means that the session has expired" — taken
        # as implying "no session" also yields 401. Unconfirmed against the live API
        # until the first verified run (same caveat as TC-002/TC-012's exact codes).
        assert unauthenticated_response.status_code == 401, (
            f"expected 401 without a token, got {unauthenticated_response.status_code}: "
            f"{unauthenticated_response.raw.text}"
        )