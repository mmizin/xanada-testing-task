"""Reusable cross-cutting assertions for authentication responses.

Per TC-019: no negative-case response may echo back a value the caller
considers sensitive (the submitted password today; a security answer or MFA
code tomorrow). Rather than a standalone API call, this is invoked *inside*
every negative test as a shared assertion — zero extra rate budget, and one
place to extend if the set of sensitive values ever grows.
"""

from __future__ import annotations

from src.infra.api.http_client import ApiResponse


def assert_no_sensitive_values_leaked(response: ApiResponse, *values: str | None) -> None:
    """Assert none of ``values`` appear anywhere in the response body, headers, or cookies.

    Falsy values (``None``, ``""``) are skipped rather than rejected, so
    callers can pass a field that may legitimately be absent (e.g. an
    omitted password in a missing-field case) without an extra ``if``.

    Cookies are checked separately from ``response.raw.cookies.jar`` rather
    than folded into the header string: this API sets ``Set-Cookie`` headers
    that ``headers.values()`` already covers as raw text, but iterating the
    jar's parsed cookie *values* also catches a leak inside an encoded/
    percent-escaped cookie value that wouldn't match a plain substring check
    against the raw header line.
    """
    body = response.raw.text
    headers = " ".join(response.raw.headers.values())
    cookies = " ".join(cookie.value or "" for cookie in response.raw.cookies.jar)
    for value in values:
        if not value:
            continue
        assert value not in body, f"sensitive value {value!r} leaked in response body: {body}"
        assert (
            value not in headers
        ), f"sensitive value {value!r} leaked in response headers: {dict(response.raw.headers)}"
        assert value not in cookies, f"sensitive value {value!r} leaked in a response cookie"
