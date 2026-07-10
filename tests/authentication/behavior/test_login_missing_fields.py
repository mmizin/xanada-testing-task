"""TC-007/TC-008/TC-009: field-presence decision table returns 400.

See test-cases/api/authentication/login.md#tc-007 (missing username),
#tc-008 (missing password), and #tc-009 (empty body / null fields) for the
full case specs.

One parametrized test rather than three near-identical functions: all four
variants are the same decision table (username x password, each
absent/present/null) exercising the same request/assert shape, differing
only in which keys ``AuthenticationApiClient.login()`` is given. Each
variant still carries its own Allure test-case ID via ``allure.dynamic`` so
the three TCs remain individually traceable in reports.
"""

from __future__ import annotations

from collections.abc import Callable

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.utils.assertions import assert_no_sensitive_values_leaked
from src.features.authentication.utils.session import extract_session_token
from src.utils.data_generators import VALID_FORMAT_PASSWORD, non_existent_username

# Builders called fresh per test (not collection time) so synthetic usernames aren't reused.
FIELD_PRESENCE_CASES: list[tuple[str, str, Callable[[], dict[str, str | None]]]] = [
    (
        "TC-007",
        "username absent, password present",
        lambda: {"password": VALID_FORMAT_PASSWORD},
    ),
    (
        "TC-008",
        "username present, password absent",
        lambda: {"username": non_existent_username()},
    ),
    ("TC-009", "both fields absent (empty body)", dict),
    (
        "TC-009",
        "both fields explicitly null",
        lambda: {"username": None, "password": None},
    ),
]


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Field presence")
@allure.severity(allure.severity_level.NORMAL)
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "testcase_id, case_label, build_kwargs",
    FIELD_PRESENCE_CASES,
    ids=[f"{tc}-{label.replace(' ', '_')}" for tc, label, _ in FIELD_PRESENCE_CASES],
)
def test_login_with_missing_or_null_fields(
    anonymous_auth_client: AuthenticationApiClient,
    testcase_id: str,
    case_label: str,
    build_kwargs: Callable[[], dict[str, str | None]],
) -> None:
    allure.dynamic.testcase(testcase_id)
    allure.dynamic.title(f"Login with {case_label} returns 400")
    kwargs = build_kwargs()

    with allure.step(f"Log in with {case_label}"):
        response = anonymous_auth_client.login(**kwargs)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 400 (or another 4xx, never 5xx)"):
        assert (
            response.status_code == 400
        ), f"expected a 4xx, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session token issued and nothing sensitive leaked"):
        assert (
            extract_session_token(response) is None
        ), f"expected no session-token for {case_label}: {response.raw.text}"
        assert_no_sensitive_values_leaked(response, kwargs.get("password"))
