"""TC-014: Login with empty-string credentials returns 400.

See test-cases/api/authentication/login.md#tc-014 for the full case spec.

Boundary Value Analysis at length 0 (FR-3.1): empty string is a distinct
partition from "field absent" (TC-007/008/009) and from "field present with
a normal value" — the field is present, JSON-valid, and a string, just of
zero length. Uses a synthetic non-existent username throughout so even an
unexpected lenient path never touches the real account.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# Concrete values (not lambdas) since empty strings can't collide with anything.
EMPTY_CREDENTIAL_CASES: list[tuple[str, str, str]] = [
    ("empty username", "", VALID_FORMAT_PASSWORD),
    ("empty password", non_existent_username(), ""),
    ("both empty", "", ""),
]


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Boundary values")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-014")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "boundary", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "case_label, username, password",
    EMPTY_CREDENTIAL_CASES,
    ids=[label.replace(" ", "_") for label, _, _ in EMPTY_CREDENTIAL_CASES],
)
def test_login_with_empty_string_credentials(
    anonymous_auth_client: AuthenticationApiClient, case_label: str, username: str, password: str
) -> None:
    allure.dynamic.title(f"Login with {case_label} returns 400")

    with allure.step(f"Log in with {case_label}"):
        response = anonymous_auth_client.login(username, password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 400, never 5xx"):
        assert (
            response.status_code == 400
        ), f"expected 400, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token and nothing sensitive leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for {case_label}: {response.raw.text}"
        assert_no_sensitive_values_leaked(response, password)
