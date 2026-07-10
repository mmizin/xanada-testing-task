"""Authentication (session) API client.

Per Architecture Design §7: knows the session resource's contract only — URL,
payload shape, and how to build deliberately malformed request variants for
negative testing (TD-001 §1 error guessing). It performs no assertions and
returns the ``ApiResponse`` untouched; validators and tests decide what
"correct" means.

Per the docs, Login (POST), Logout (DELETE), and Session (GET) all operate on
the same ``/bpapi/rest/security/session`` resource — one bounded context
(Authentication), not three unrelated endpoints — so they live on one client.
"""

from __future__ import annotations

from typing import Any

from src.infra.api.http_client import ApiHttpClient, ApiResponse

SESSION_PATH = "/bpapi/rest/security/session"

# Endpoint-specific headers; no common header across all session operations.
_LOGIN_HEADERS = {"content-type": "application/json;charset=UTF-8", "accept": "*/*"}
_SESSION_HEADERS = {"accept": "application/json", "User-Agent": "api-doc-test-client"}

# Sentinel to distinguish "omitted field" from "explicit null" (separate equivalence classes).
_OMIT = object()


class AuthenticationApiClient:
    """Builds requests against the authentication/session endpoint."""

    def __init__(self, http_client: ApiHttpClient) -> None:
        self._http = http_client

    @property
    def http_client(self) -> ApiHttpClient:
        """The underlying transport client; exposed for auth-state isolation verification."""
        return self._http

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
        headers = _LOGIN_HEADERS | httpx_kwargs.pop("headers", {})
        response = self._http.post(SESSION_PATH, json=body, headers=headers, **httpx_kwargs)

        return response

    def login_with_raw_body(
        self,
        content: str | bytes,
        *,
        headers: dict[str, str] | None = None,
        **httpx_kwargs: Any,
    ) -> ApiResponse:
        """POST raw content, bypassing JSON encoding.

        Needed for invalid JSON bodies and custom Content-Type headers.
        """
        merged_headers = _LOGIN_HEADERS | (headers or {})
        response = self._http.post(SESSION_PATH, content=content, headers=merged_headers, **httpx_kwargs)

        return response

    def get_session(
        self,
        session_token: Any = _OMIT,
        **httpx_kwargs: Any,
    ) -> ApiResponse:
        """GET current session status.

        200 = valid/active; 401 = expired. Proves issued tokens authenticate.
        """
        headers = dict(_SESSION_HEADERS)
        if session_token is not _OMIT:
            headers["session-token"] = session_token
        headers |= httpx_kwargs.pop("headers", {})
        return self._http.get(SESSION_PATH, headers=headers, **httpx_kwargs)

