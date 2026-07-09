"""TC-015: Login with whitespace-padded credentials does not authenticate.

See test-cases/api/authentication/login.md#tc-015 for the full case spec.

Boundary Value Analysis at the whitespace edge (FR-3.1): pads a synthetic
non-existent username with leading/trailing spaces rather than the real
username, deliberately. If the API trims input server-side, a padded *real*
username paired with a wrong password would still be a genuine failed
login against the real account — spending one of its three strikes just to
find out whether trimming happens. A non-existent username sidesteps that
risk entirely while still answering the question: does padding change the
outcome for what is otherwise the same logical username?
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
@allure.story("Boundary values")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Login with whitespace-padded credentials does not authenticate")
@allure.testcase("TC-015")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "boundary", "auth")
@pytest.mark.negative
@pytest.mark.login
def test_login_with_whitespace_padded_username(
    anonymous_auth_client: AuthenticationApiClient,
) -> None:
    base_username = non_existent_username()
    padded_username = f"  {base_username}\t\n"
    password = VALID_FORMAT_PASSWORD

    with allure.step("Log in with the unpadded synthetic username (baseline)"):
        baseline = anonymous_auth_client.login(base_username, password)
        allure.attach(
            str(baseline), name="Baseline response", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Log in with the same username padded with leading/trailing whitespace"):
        padded = anonymous_auth_client.login(padded_username, password)
        allure.attach(
            str(padded), name="Padded response", attachment_type=allure.attachment_type.TEXT
        )

    with allure.step("Assert both are rejected, never a server error"):
        for label, response in (("unpadded", baseline), ("padded", padded)):
            assert (
                response.status_code == 400
            ), f"expected 400 for {label} username, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert padding doesn't change the outcome (same status, same error shape)"):
        assert baseline.status_code == padded.status_code, (
            f"padding changed the status code: unpadded={baseline.status_code}, "
            f"padded={padded.status_code} — suggests the API trims and treats the "
            f"padded value as a different (and differently handled) username"
        )
        assert type(baseline.data) is type(
            padded.data
        ), "padding changed the error body shape between unpadded and padded variants"

    with allure.step("Assert no session token issued and nothing sensitive leaked"):
        for response in (baseline, padded):
            assert (
                extract_session_token(response) is None
            ), f"expected no session-token for a non-existent user: {response.raw.text}"
            assert_no_sensitive_values_leaked(response, password)
