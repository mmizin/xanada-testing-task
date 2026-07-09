"""TC-004: Repeated valid logins behave consistently.

See test-cases/api/authentication/login.md#tc-004 for the full case spec.

Single-endpoint (two sequential POSTs to the same login resource), so this
lives in behavior/ rather than integration/ — the login.md doc tags this
@integration, but the codebase's `integration` pytest marker is explicitly
defined as "cross-endpoint" (pyproject.toml) and reserved for cases like
TC-003/TC-024 that chain login with a second, different endpoint. Applying
that marker here would stretch its meaning, so it's deliberately omitted.

Each login uses its own fresh client (own httpx.Client/cookie jar), like
``anonymous_auth_client``. A shared client would carry the first login's
session cookie into the second request, conflating "do valid credentials
work again from a clean state" (what this case tests) with "does an
already-authenticated client's login behave differently" (a different,
undocumented question the docs don't address).
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.models.login_response import LoginResponse
from src.infra.api.http_client import ApiHttpClient
from src.infra.config import Settings


def _login_from_clean_client(settings: Settings, label: str) -> LoginResponse:
    """Log in on a brand-new client and return the validated response.

    Shared by both logins below so each gets its own fresh ``httpx.Client``
    (see the module docstring for why that isolation matters), without
    duplicating the status/schema checks for each one. A raw
    ``ValidationError`` (unhandled) already fails the test with pydantic's
    own diagnostics, including which field/type didn't match — no need to
    re-wrap it.
    """
    with ApiHttpClient(base_url=settings.base_url) as http_client:
        client = AuthenticationApiClient(http_client)
        response = client.login(settings.username, settings.password)

    allure.attach(str(response), name=f"{label} response", attachment_type=allure.attachment_type.TEXT)
    assert response.status_code == 200, f"expected 200, got {response.status_code}: {response.raw.text}"

    return LoginResponse.model_validate(response.data)


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Reliability")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Repeated valid logins behave consistently")
@allure.testcase("TC-004")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "auth")
@pytest.mark.positive
@pytest.mark.login
def test_repeated_valid_logins_are_consistent(settings: Settings) -> None:
    with allure.step("First login (clean client)"):
        first = _login_from_clean_client(settings, "First")

    with allure.step("Second login (separate clean client)"):
        second = _login_from_clean_client(settings, "Second")

    with allure.step("Record (not assert) token reuse semantics"):
        # Whether a second login reissues the same token or mints a new one is
        # an observed contract detail, not a documented guarantee (docs are
        # silent on it) — recorded as evidence for whoever reads this run,
        # not asserted one way or the other (FR-4.1 only requires consistency
        # of status/schema, not a specific session-identity policy).
        allure.attach(
            f"same token reused: {first.session_token == second.session_token}",
            name="Token reuse observation",
            attachment_type=allure.attachment_type.TEXT,
        )