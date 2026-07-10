"""TC-011: Login with wrong field types returns 400.

See test-cases/api/authentication/login.md#tc-011 for the full case spec.

One parametrized test over the type-confusion variants (Error Guessing,
FR-2.4): each sends a syntactically valid JSON body — ``login()``'s
``username``/``password`` params are typed ``Any`` precisely so a test can
hand it a number, object, or array and let httpx serialize it as-is.
"""

from __future__ import annotations

from typing import Any

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# One field wrong-typed per variant for failure isolation.
WRONG_TYPE_CASES: list[tuple[str, Any, Any]] = [
    ("username as number", 12345, VALID_FORMAT_PASSWORD),
    ("username as object", {"nested": "value"}, VALID_FORMAT_PASSWORD),
    ("username as array", ["a", "b"], VALID_FORMAT_PASSWORD),
    ("password as number", non_existent_username(), 12345),
]


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Malformed input")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-011")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "case_label, username, password",
    WRONG_TYPE_CASES,
    ids=[label.replace(" ", "_") for label, _, _ in WRONG_TYPE_CASES],
)
def test_login_with_wrong_field_types(
    anonymous_auth_client: AuthenticationApiClient, case_label: str, username: Any, password: Any
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
        # Only string passwords can leak as-is; non-strings never round-trip literally.
        if isinstance(password, str):
            assert_no_sensitive_values_leaked(response, password)
