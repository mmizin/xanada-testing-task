"""TC-017: Login with unicode and special characters is handled cleanly.

See test-cases/api/authentication/login.md#tc-017 for the full case spec.

Error Guessing on encoding (FR-3.1): multibyte unicode, combining marks, and
JSON control-character escapes are a classic source of encode/decode bugs
(mojibake, truncation at a byte boundary that splits a multibyte character,
or a 500 from an unhandled decoding exception) that plain-ASCII negative
cases never exercise. All variants use a synthetic non-existent username so
even mis-handled encoding can't accidentally normalize into a collision
with the real account's username.
"""

from __future__ import annotations

import json

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# Each entry: (case label, username suffix). The synthetic-unique prefix from
# non_existent_username() is kept so the whole value stays guaranteed unused,
# with the unicode/special content appended to actually exercise encoding.
UNICODE_CASES: list[tuple[str, str]] = [
    ("CJK characters", "-你好世界"),  # 你好世界
    ("emoji", "-\U0001f600\U0001f680"),  # 😀🚀
    ("combining characters", "-é̀̂"),  # e + combining accents
    ("JSON control-character escapes", "-\t\n\r\x00"),
]


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Boundary values")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-017")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "boundary", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "case_label, suffix",
    UNICODE_CASES,
    ids=[label.replace(" ", "_") for label, _ in UNICODE_CASES],
)
def test_login_with_unicode_and_special_characters(
    anonymous_auth_client: AuthenticationApiClient, case_label: str, suffix: str
) -> None:
    allure.dynamic.title(f"Login with {case_label} in username is handled cleanly")
    username = f"{non_existent_username()}{suffix}"
    password = VALID_FORMAT_PASSWORD

    with allure.step(f"Log in with a username containing {case_label}"):
        response = anonymous_auth_client.login(username, password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 400, never 5xx"):
        assert (
            response.status_code == 400
        ), f"expected 400, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert the response body is valid JSON, no mojibake artifacts"):
        try:
            json.loads(response.raw.text)
        except ValueError as exc:
            pytest.fail(
                f"response body is not valid JSON for {case_label}: {exc}\n{response.raw.text}"
            )

    with allure.step("Assert no session token and nothing sensitive leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for {case_label}: {response.raw.text}"
        assert_no_sensitive_values_leaked(response, password)
