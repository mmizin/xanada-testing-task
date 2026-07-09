"""TC-005: Login with a non-existent username returns 400 without a token.

See test-cases/api/authentication/login.md#tc-005 for the full case spec.
Uses a synthetic, never-before-used username (src/utils/data_generators.py)
rather than the real account, per TD-001 §5: negative-credential cases must
not spend one of the real account's three failed-login strikes.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Invalid credentials")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Login with a non-existent username returns 400 without a token")
@allure.testcase("TC-005")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "auth")
@pytest.mark.negative
@pytest.mark.login
def test_login_with_nonexistent_username(anonymous_auth_client: AuthenticationApiClient) -> None:
    username = non_existent_username()
    password = VALID_FORMAT_PASSWORD

    with allure.step("Log in with a syntactically valid but non-existent username"):
        response = anonymous_auth_client.login(username, password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert the request is rejected, never a server error"):
        assert (
            response.status_code == 400
        ), f"expected a 4xx, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token is issued"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for a non-existent user: {response.raw.text}"
        assert "session-token" not in response.cookie_names, (
            f"expected no session-token cookie for a non-existent user, "
            f"got: {response.cookie_names}"
        )

    with allure.step("Assert the submitted password is never echoed back"):
        assert_no_sensitive_values_leaked(response, password)
