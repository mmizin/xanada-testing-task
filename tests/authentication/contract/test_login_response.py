"""TC-002: Successful login response matches the documented schema.

See test-cases/api/authentication/login.md#tc-002 for the full case spec.
"""

from __future__ import annotations

import allure
import pytest

from src.features.authentication.api.authentication_client import AuthenticationApiClient
from src.features.authentication.models.login_response import LoginResponse
from src.infra.config import Settings


@allure.epic("Authentication")
@allure.feature("Login")
@allure.story("Response contract")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Successful login response matches the documented schema")
@allure.testcase("TC-002")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
@allure.tag("regression", "contract", "auth")
@pytest.mark.positive
@pytest.mark.login
def test_login_response_matches_documented_schema(
    settings: Settings, auth_client: AuthenticationApiClient
) -> None:
    with allure.step("Log in with the configured real account credentials"):
        response = auth_client.login(settings.username, settings.password)
        allure.attach(str(response), name="Response", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Assert 200 OK"):
        assert response.status_code == 200, f"expected 200, got {response.status_code}: {response.raw.text}"

    with allure.step(
        "Assert the body has exactly the documented fields, correctly typed"
    ):
        # An unhandled ValidationError already fails the test with pydantic's
        # own diagnostics (which field/type didn't match) — no need to re-wrap it.
        LoginResponse.model_validate(response.data)
