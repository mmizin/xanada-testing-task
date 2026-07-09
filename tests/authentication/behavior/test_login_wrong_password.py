"""TC-006: Wrong password for the real account returns 400, then recovery
login succeeds.

See test-cases/api/authentication/login.md#tc-006 for the full case spec.

Isolation: account-state, atomic (TD-001 §3.2). This is the *only* case
allowed to spend a strike against the real account's 3-consecutive-failure
suspension counter, and it does so exactly once per suite run, immediately
followed by a correct-credentials login that resets the counter. If that
recovery login itself fails, the whole run aborts rather than retrying —
per Architecture Design §10, a retry storm here is how the account gets
suspended for everyone sharing it.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.infra.config import Settings


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Invalid credentials")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Wrong password for the real account returns 400, then recovery login succeeds")
@allure.testcase("TC-006")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "security", "auth")
@pytest.mark.negative
@pytest.mark.login
def test_wrong_password_then_recovery_login(
    settings: Settings, auth_client: AuthenticationApiClient
) -> None:
    wrong_password = f"{settings.password}-wrong"

    with allure.step("Log in with the real username and a deliberately wrong password"):
        failure_response = auth_client.login(settings.username, wrong_password)
        allure.attach(
            str(failure_response),
            name="Failure response",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Assert the failure looks like any other invalid-credentials error"):
        # Same shape as TC-005's non-existent-user error: a generic 4xx that
        # doesn't reveal "user exists, password wrong" vs "user doesn't
        # exist" (the enumeration guard, FR-2.1/FR-2.2) — asserted here the
        # same way TC-005 asserts it, not diffed byte-for-byte against a
        # separately captured response.
        assert (
            400 <= failure_response.status_code < 500
        ), f"expected a 4xx, got {failure_response.status_code}: {failure_response.raw.text}"
        assert (
            extract_session_token(failure_response) is None
        ), f"expected no session-token on a failed login: {failure_response.raw.text}"
        assert_no_sensitive_values_leaked(failure_response, settings.password, wrong_password)

    with allure.step("Recovery: log in again with the correct password"):
        # Uses the same auth_client instance deliberately: this is a real
        # sequential recovery of one account, not an isolation concern (unlike
        # TC-003's anonymous-client control) — the point is that the *account*
        # is usable again, regardless of which client asks.
        recovery_response = auth_client.login(settings.username, settings.password)
        allure.attach(
            str(recovery_response),
            name="Recovery response",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Assert recovery succeeded (abort-worthy if not)"):
        assert recovery_response.status_code == 200, (
            "recovery login failed after the deliberate wrong-password attempt — "
            f"aborting is safer than retrying (Architecture Design §10): "
            f"got {recovery_response.status_code}: {recovery_response.raw.text}"
        )
        assert extract_session_token(
            recovery_response
        ), f"expected a non-empty session-token on recovery: {recovery_response.raw.text}"
