"""Helpers for interpreting login responses.

Per the docs (PRD-001 §"Endpoint under test") and its sample code
(`return data['session-token']`), a successful login always returns the token
as this body key. "cookie or header named session-token" in the docs describes
how callers *send* it back on later requests — not how the login response
itself delivers it — so this only reads the body.
"""

from __future__ import annotations

from src.infra.api.http_client import ApiResponse

SESSION_TOKEN_KEY = "session-token"


def extract_session_token(response: ApiResponse) -> str | None:
    """Return the session token from a successful login response's body."""
    if not isinstance(response.data, dict):
        return None
    token = response.data.get(SESSION_TOKEN_KEY)
    return str(token) if token else None