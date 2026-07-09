"""TC-016: Login with very long credential values is rejected cleanly.

See test-cases/api/authentication/login.md#tc-016 for the full case spec.

Boundary Value Analysis at the extreme-length end (FR-3.1): an oversized
field is a classic vector for both broken input validation (a 5xx from an
unhandled length check) and resource-exhaustion behavior (a hung or slow
request). Both a "large" (~1,000 char) and a "very large" (~10,000 char)
value are exercised per field to see whether the boundary is crossed
gracefully at both magnitudes, not just the first one tried. Only the
username values are synthetic-unique per generation; the long password is a
repeated-character string since its content doesn't need to be unique, only
long.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.infra.api.http_client import DEFAULT_TIMEOUT
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# Each entry: (case label, username, password). "Large" and "very large"
# are distinct partitions in their own right (BVA doesn't stop at one
# extreme) — a validator with an off silent cutoff might reject one length
# and 500 on the other.
LONG_CREDENTIAL_CASES: list[tuple[str, str, str]] = [
    ("username ~1,000 chars", f"{non_existent_username()}{'a' * 1000}", VALID_FORMAT_PASSWORD),
    ("username ~10,000 chars", f"{non_existent_username()}{'a' * 10_000}", VALID_FORMAT_PASSWORD),
    ("password ~1,000 chars", non_existent_username(), "p" * 1000),
    ("password ~10,000 chars", non_existent_username(), "p" * 10_000),
]

# The read timeout is the hard ceiling below which a response must arrive
# (ADR-002: fail-fast, no indefinite blocking); asserting comfortably under
# it documents that long input doesn't measurably degrade the endpoint,
# not just that it eventually responds before the client gives up.
_TIMEOUT_BUDGET_MS = DEFAULT_TIMEOUT.read * 1000 if DEFAULT_TIMEOUT.read else None


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Boundary values")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-016")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "boundary", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "case_label, username, password",
    LONG_CREDENTIAL_CASES,
    ids=[label.replace(" ", "_").replace(",", "") for label, _, _ in LONG_CREDENTIAL_CASES],
)
def test_login_with_long_credentials(
    anonymous_auth_client: AuthenticationApiClient, case_label: str, username: str, password: str
) -> None:
    allure.dynamic.title(f"Login with {case_label} is rejected cleanly")

    with allure.step(f"Log in with {case_label}"):
        response = anonymous_auth_client.login(username, password)
        allure.attach(
            f"{response!s}\nelapsed_ms={response.elapsed_ms:.0f}",
            name="Response",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Assert 400 or 413, never 5xx"):
        assert response.status_code in (
            400,
            413,
        ), f"expected 400 or 413, got {response.status_code}: {response.raw.text[:500]}"

    with allure.step("Assert the response arrived well within the client's read timeout"):
        if _TIMEOUT_BUDGET_MS is not None:
            assert response.elapsed_ms < _TIMEOUT_BUDGET_MS, (
                f"response took {response.elapsed_ms:.0f} ms, close to/over the "
                f"{_TIMEOUT_BUDGET_MS:.0f} ms read timeout — long input may be "
                f"degrading the endpoint"
            )

    with allure.step("Assert no session token and nothing sensitive leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for {case_label}: {response.raw.text[:500]}"
        assert_no_sensitive_values_leaked(response, password)
