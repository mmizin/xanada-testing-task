"""Login endpoint API client.

Per Architecture Design §7: knows the login endpoint's contract only — URL, payload
shape, and how to build deliberately malformed request variants for negative
testing (TD-001 §1 error guessing). It performs no assertions and returns the
``ApiResponse`` untouched; validators and tests decide what "correct" means.
"""

from __future__ import annotations

from typing import Any

from src.infra.api.http_client import ApiHttpClient, ApiResponse

LOGIN_PATH = "/bpapi/rest/security/session"

# Sentinel distinct from None: lets callers express "field omitted from the
# body entirely" separately from "field explicitly set to null" — these are
# different equivalence classes in the decision table (TD-001 §1, TC-007/008/009).
_OMIT = object()


class LoginApiClient:
    """Builds requests against the login/session endpoint."""

    def __init__(self, http_client: ApiHttpClient) -> None:
        self._http = http_client

    def login(
        self,
        username: Any = _OMIT,
        password: Any = _OMIT,
        **httpx_kwargs: Any,
    ) -> ApiResponse:
        """POST a JSON login request.

        Leaving a parameter at its default (_OMIT) drops the key from the body
        entirely (missing-field case); passing ``None`` sends an explicit JSON
        null; passing ``""`` sends an empty string. Three distinct partitions,
        one method — callers pick the case they want by what they pass.
        """
        body: dict[str, Any] = {}
        if username is not _OMIT:
            body["username"] = username
        if password is not _OMIT:
            body["password"] = password
        response = self._http.post(LOGIN_PATH, json=body, **httpx_kwargs)

        return response

    def login_with_raw_body(
        self,
        content: str | bytes,
        *,
        headers: dict[str, str] | None = None,
        **httpx_kwargs: Any,
    ) -> ApiResponse:
        """POST arbitrary raw content, bypassing JSON encoding entirely.

        Needed for cases httpx's ``json=`` helper can't produce by construction:
        syntactically invalid JSON bodies (TC-010) and a wrong Content-Type header
        wrapping an otherwise valid-shaped body (TC-012).
        """
        response = self._http.post(LOGIN_PATH, content=content, headers=headers, **httpx_kwargs)

        return response

