"""TC-010: Login with syntactically invalid JSON returns 400.

See test-cases/api/authentication/login.md#tc-010 for the full case spec.

Uses ``login_with_raw_body`` rather than ``login`` — the latter always
serializes a valid Python dict to valid JSON via httpx's ``json=`` helper, so
it can never produce a truncated/malformed body by construction. This case
needs a raw, deliberately broken string on the wire.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.session import extract_session_token

# Truncated JSON to exercise syntax error handling.
_TRUNCATED_JSON_BODY = '{"username": "x", '


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Malformed input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Login with syntactically invalid JSON returns 400")
@allure.testcase("TC-010")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
def test_login_with_invalid_json(anonymous_auth_client: AuthenticationApiClient) -> None:
    with allure.step("POST a truncated/invalid JSON body"):
        response = anonymous_auth_client.login_with_raw_body(_TRUNCATED_JSON_BODY)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 400, never 5xx"):
        assert (
            response.status_code == 400
        ), f"expected 400, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token, and no parser internals leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for an invalid-JSON body: {response.raw.text}"
        # Parser stack traces leak internals via language/framework names.
        lowered_body = response.raw.text.lower()
        for leak_marker in ("traceback", "stacktrace", "exception", "at com.", "at java.", "  at "):
            assert (
                leak_marker not in lowered_body
            ), f"response looks like it leaked parser internals ({leak_marker!r}): {response.raw.text}"
