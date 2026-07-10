"""TC-013 (follow-up): Authenticated PUT/PATCH on the session URL return 405.

See test-cases/api/authentication/login.md#tc-013 for the full case spec.

Lives under ``integration/``, not ``behavior/``: like TC-003/TC-024, this
chains a login (POST) with a second operation on the session resource — the
`integration` marker's cross-operation definition established by those cases
(see ``tests/authentication/behavior/test_login_repeated.py``'s docstring).

Exists specifically to isolate a claim the unauthenticated variant
(``tests/authentication/behavior/test_login_wrong_http_methods.py``) can't
make on its own: a credential-less PUT/PATCH returns 401 there. Observed
behavior only — nothing is known here about the backend's internal
middleware order — but that observation alone leaves "PUT/PATCH are
unsupported methods" unconfirmed: a request could be rejected for either
reason (no credentials, or wrong method) and a 401 wouldn't tell you which.
Authenticating first removes auth-state as a possible cause, so a 405 here
confirms method support specifically, **not** authentication itself (login's
own correctness is TC-001/TC-002's job, not this test's).

**Authentication-source isolation:** the PUT/PATCH call deliberately runs on
a fresh, cookie-free ``ApiHttpClient`` (own httpx.Client, empty cookie jar),
never the client that performed the login. Reusing the login's client would
leave both an explicit ``session-token`` header *and* the Set-Cookie the
login response sets on that instance — passing would then prove nothing
about which one authenticated the request (see ``ApiHttpClient``'s
docstring on cookie persistence, and TC-003/TC-024's isolation notes for the
same pitfall). A client that has never made a request has no cookies to
leak, so success here is attributable to the explicit header alone, i.e.
this validates header-based auth specifically, not the cookie-based path
(cookie auth is TC-024's concern).

**Why the token isn't separately verified via GET session before asserting
405:** that would duplicate TC-003, which already establishes "a token from
login authenticates a real request." It would also be redundant here
specifically: based on the observed responses above, an invalid token
produces 401, not 405 — so getting 405 instead of 401 is itself evidence the
token was accepted as valid before whatever rejected the method ran. A
separate confirmation call would spend rate budget to reconfirm something a
405 result already implies.
"""

from __future__ import annotations

from collections.abc import Callable

import allure
import pytest

from src.features.authentication.api.authentication_client import (
    SESSION_PATH,
    AuthenticationApiClient,
)
from src.features.authentication.utils.session import extract_session_token
from src.infra.api.http_client import ApiHttpClient, ApiResponse
from src.infra.config import Settings

# Via ApiHttpClient with explicit session-token header; no feature-client wrapper.
AUTHENTICATED_METHOD_VARIANTS: list[tuple[str, Callable[[ApiHttpClient, str], ApiResponse]]] = [
    ("PUT", lambda client, token: client.put(SESSION_PATH, headers={"session-token": token})),
    ("PATCH", lambda client, token: client.patch(SESSION_PATH, headers={"session-token": token})),
]


@pytest.fixture()
def valid_session_token(
    settings: Settings, http_client_factory: Callable[[], ApiHttpClient]
) -> str:
    """Log in and return a valid session token for one test.

    Function-scoped: each parametrized variant logs in separately.
    Cost is minimal and paced by the shared rate limiter (ADR-004).
    """
    with http_client_factory() as login_client:
        login_response = AuthenticationApiClient(login_client).login(
            settings.username, settings.password
        )
        assert login_response.status_code == 200, (
            "expected 200 obtaining a token for the PUT/PATCH checks, got "
            f"{login_response.status_code}: {login_response.raw.text}"
        )
        token = extract_session_token(login_response)
        assert token, f"expected a non-empty session-token: {login_response.raw.text}"
    return token


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Protocol misuse")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-013")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.integration
@pytest.mark.parametrize(
    "method_name, send_authenticated_request",
    AUTHENTICATED_METHOD_VARIANTS,
    ids=[name for name, _ in AUTHENTICATED_METHOD_VARIANTS],
)
def test_wrong_http_method_with_valid_session_returns_405(
    http_client_factory: Callable[[], ApiHttpClient],
    valid_session_token: str,
    method_name: str,
    send_authenticated_request: Callable[[ApiHttpClient, str], ApiResponse],
) -> None:
    allure.dynamic.title(f"Authenticated {method_name} on the session URL returns 405")

    with allure.step(f"Send a header-authenticated {method_name} via a cookie-free client"):
        # Fresh cookie-free client isolates auth source; still shares rate limiter (ADR-004).
        with http_client_factory() as cookie_free_client:
            response = send_authenticated_request(cookie_free_client, valid_session_token)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 405 Method Not Allowed"):
        # Valid token + no cookies = method rejection only, not auth issues.
        assert response.status_code == 405, (
            f"expected 405 for authenticated {method_name}, got "
            f"{response.status_code}: {response.raw.text}"
        )
