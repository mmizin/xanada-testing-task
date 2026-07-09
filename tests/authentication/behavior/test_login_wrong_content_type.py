"""TC-012: Login with wrong Content-Type is rejected.

See test-cases/api/authentication/login.md#tc-012 for the full case spec.

Uses ``login_with_raw_body`` with an explicit Content-Type override: the
body itself is valid-shaped JSON (synthetic, non-existent credentials) —
only the header claims a different media type, isolating "wrong
Content-Type" from "malformed body" (already covered by TC-010).
"""

from __future__ import annotations

import json

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Malformed input")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Login with wrong Content-Type is rejected")
@allure.testcase("TC-012")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
def test_login_with_wrong_content_type(anonymous_auth_client: AuthenticationApiClient) -> None:
    username = non_existent_username()
    body = json.dumps({"username": username, "password": VALID_FORMAT_PASSWORD})

    with allure.step("POST a valid-shaped body with Content-Type: text/plain"):
        response = anonymous_auth_client.login_with_raw_body(
            body, headers={"content-type": "text/plain"}
        )
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 400 or 415, never 5xx"):
        # Spec leaves the exact code open (400 or 415) — unlike TC-010/TC-011,
        # which name a single confirmed code — since Content-Type rejection is
        # commonly implemented as either "reject at the framework/media-type
        # layer" (415) or "reject at the login validator" (400).
        assert response.status_code in (
            400,
            415,
        ), f"expected 400 or 415, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token and nothing sensitive leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for a wrong Content-Type request: {response.raw.text}"
        assert_no_sensitive_values_leaked(response, VALID_FORMAT_PASSWORD)
