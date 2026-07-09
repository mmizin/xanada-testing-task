"""TC-018: Injection-style payloads are rejected without leaking internals.

See test-cases/api/authentication/login.md#tc-018 for the full case spec.

Error Guessing on security-sensitive inputs (FR-3.2): SQL-style, NoSQL
operator-style, and path/template-injection payloads are the classic
blackbox probes for "does unsanitized input reach a query/interpreter
layer." A blackbox suite can't prove the backend is *not* vulnerable, only
that these specific payloads don't produce an observable symptom (a 5xx, a
leaked stack trace, an unexpectedly successful auth) — which is exactly
what's asserted here. All variants are synthetic and non-existent so a
payload that *did* somehow succeed wouldn't be mistaken for a real-account
compromise.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# Each entry: (case label, username, password). A payload is injected into
# whichever field a real attacker would most plausibly target for that
# style, keeping the other field a normal synthetic value so a failure
# clearly implicates the injected field.
INJECTION_CASES: list[tuple[str, str, str]] = [
    ("SQL tautology in username", "' OR '1'='1", VALID_FORMAT_PASSWORD),
    ("SQL comment-terminated username", "admin'--", VALID_FORMAT_PASSWORD),
    ("SQL tautology in password", non_existent_username(), "' OR '1'='1"),
    ("embedded quotes in username", f"{non_existent_username()}\"'", VALID_FORMAT_PASSWORD),
    ("NoSQL operator-style password", non_existent_username(), '{"$gt": ""}'),
    ("path traversal in username", "../../etc/passwd", VALID_FORMAT_PASSWORD),
    ("template injection in username", "{{7*7}}", VALID_FORMAT_PASSWORD),
]

# Internals that must never appear in an error body regardless of which
# payload triggered it — the negative-case counterpart to TC-019's
# password-echo check, but for backend-implementation leakage rather than
# credential leakage.
_INTERNAL_LEAK_MARKERS = (
    "Traceback",
    "SQLException",
    "SQLSyntaxErrorException",
    "at java.",
    "at org.springframework",
    "stacktrace",
)


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Security")
@allure.severity(allure.severity_level.CRITICAL)
@allure.testcase("TC-018")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "security", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "case_label, username, password",
    INJECTION_CASES,
    ids=[label.replace(" ", "_") for label, _, _ in INJECTION_CASES],
)
def test_login_with_injection_style_payloads(
    anonymous_auth_client: AuthenticationApiClient, case_label: str, username: str, password: str
) -> None:
    allure.dynamic.title(f"Login with {case_label} is rejected without leaking internals")

    with allure.step(f"Log in with {case_label}"):
        response = anonymous_auth_client.login(username, password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 4xx, never 5xx"):
        assert (
            400 <= response.status_code < 500
        ), f"expected a 4xx, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token is issued"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for {case_label}: {response.raw.text}"

    with allure.step("Assert no stack traces, SQL fragments, or framework names in the error body"):
        body = response.raw.text
        for marker in _INTERNAL_LEAK_MARKERS:
            assert marker not in body, f"internal implementation detail {marker!r} leaked: {body}"

    with allure.step("Assert the submitted payload is not echoed back"):
        assert_no_sensitive_values_leaked(response, password)
        assert (
            username not in response.raw.text
        ), f"submitted username payload echoed back verbatim in the response: {response.raw.text}"
