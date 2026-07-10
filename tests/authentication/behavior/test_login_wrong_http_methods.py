"""TC-013: Wrong HTTP methods on the session URL are rejected.

See test-cases/api/authentication/login.md#tc-013 for the full case spec.

Per the docs, POST/GET/DELETE on this resource are all documented operations
(login, session-status check, logout respectively). DELETE is excluded from
this case for that reason, and GET is excluded too: an unauthenticated GET
is already exercised as the control assertion in TC-003, and re-running it
here would duplicate that authentication-state check rather than test method
support — GET is not a "wrong method" for this resource at all. Only PUT and
PATCH have no documented meaning here, so they're the only variants left.
They go through the transport layer directly (``AuthenticationApiClient``
has no ``put``/``patch`` method, by design: nothing legitimate maps to
them).

**Observed contract detail (confirmed against the live API, not the spec's
original "expected 405" guess):** a credential-less PUT/PATCH returns 401,
the same code TC-003 observes for a credential-less GET — not 405. This is
an observation about the responses, not a claim about the backend's
internal middleware order, but it's enough to show this stateless,
unauthenticated case only proves "no credentials, wrong method -> still
rejected," not "PUT/PATCH are specifically unsupported methods."

That distinct claim — method support, isolated from auth state — is covered
separately by ``tests/authentication/integration/test_login_wrong_http_methods.py``
(authenticated PUT/PATCH -> 405), which is why it lives under ``integration/``
rather than here: it chains a login with a second operation on the session
resource, matching this codebase's cross-operation definition of
``integration`` (see TC-003/TC-024).
"""

from __future__ import annotations

from collections.abc import Callable

import allure
import pytest

from src.features.authentication.api.authentication_client import (
    SESSION_PATH,
    AuthenticationApiClient,
)
from src.infra.api.http_client import ApiResponse

# Sent via ApiHttpClient directly; neither method is a feature-client operation.
METHOD_VARIANTS: list[tuple[str, Callable[[AuthenticationApiClient], ApiResponse]]] = [
    ("PUT", lambda client: client.http_client.put(SESSION_PATH)),
    ("PATCH", lambda client: client.http_client.patch(SESSION_PATH)),
]


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Protocol misuse")
@allure.severity(allure.severity_level.NORMAL)
@allure.testcase("TC-013")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "negative", "contract", "auth")
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "method_name, send_request",
    METHOD_VARIANTS,
    ids=[name for name, _ in METHOD_VARIANTS],
)
def test_wrong_http_method_on_session_url(
    anonymous_auth_client: AuthenticationApiClient,
    method_name: str,
    send_request: Callable[[AuthenticationApiClient], ApiResponse],
) -> None:
    allure.dynamic.title(f"{method_name} on the session URL is rejected")

    with allure.step(f"Send a credential-less {method_name} to the session URL"):
        response = send_request(anonymous_auth_client)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 401 (observed live behavior, not the spec's guessed 405)"):
        # Confirmed against live API: unauthenticated requests return 401 regardless of method.
        assert (
            response.status_code == 401
        ), f"expected 401 for {method_name}, got {response.status_code}: {response.raw.text}"

    with allure.step("Assert no session was created"):
        assert "session-token" not in response.cookie_names, (
            f"{method_name} unexpectedly created a session "
            f"(cookies: {response.cookie_names}): {response.raw.text}"
        )
