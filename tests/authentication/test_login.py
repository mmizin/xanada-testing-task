"""TC-001: Login with valid credentials returns 200 and a session token.

See test-cases/api/authentication/login.md#tc-001 for the full case spec.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.login_client import LoginApiClient
from src.features.authentication.utils.session import extract_session_token
from src.infra.config import Settings


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Valid credentials")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Login with valid credentials returns 200 and a session token")
@allure.testcase("TC-001")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("smoke", "critical", "contract", "auth")
@pytest.mark.positive
@pytest.mark.login
def test_login_with_valid_credentials(settings: Settings, login_client: LoginApiClient) -> None:
    with allure.step("Log in with the configured real account credentials"):
        response = login_client.login(settings.username, settings.password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 200 OK"):
        assert response.status_code == 200

    with allure.step("Assert a non-empty session token is issued"):
        token = extract_session_token(response)
        assert token, "expected a non-empty session-token in the response body"

    with allure.step("Assert the password is never echoed back"):
        assert settings.password not in response.raw.text
        assert settings.password not in "".join(response.raw.headers.values())