"""Thin infrastructure wrapper around ``httpx.Client``.

Per Architecture Design §7 and ADR-002, this is the *only* component that talks to
the network. It owns purely transport-level concerns — base URL, timeout defaults,
request timing/logging, and the ``event_hooks`` attachment points httpx exposes on
every request/response. Those hooks are where cross-cutting safety controls (the
shared rate limiter, ADR-004) and evidence capture (redacted Allure attachments)
get wired in later, without this class or any API client needing to change.
Feature API clients depend on this wrapper; it has no knowledge of any specific
endpoint or feature.

Deliberately NOT included, even though they're common in general-purpose API
clients:

- **Automatic retries.** Architecture Design §10 requires abort-fast behavior for
  login calls — a retry storm is exactly how the shared account gets suspended,
  and local retry backoff would spend requests the cross-process rate limiter
  (ADR-004) never budgeted for. Retries belong (if anywhere) in a feature-level
  service for genuinely idempotent, non-login calls — never in this shared client.
- **Raising on 4xx/5xx.** Most of this suite's cases *expect* 4xx and assert on
  the error body (TD-001 negative/edge cases). Raising by default would turn
  every one of those into exception-handling boilerplate instead of a plain
  assertion. Callers always get the response back, untouched.

Cookie behavior (important for auth-state isolation): each ``ApiHttpClient``
wraps one ``httpx.Client``, and httpx.Client persists cookies set by the
server (e.g. a session endpoint's ``Set-Cookie: session-token=...``) across
every subsequent request made on *that instance* — this is httpx's default,
not something this wrapper adds or can silently opt out of via a method call.
Two consequences for callers:

- Authentication can happen via an explicit request header *or* via a cookie
  silently carried over from an earlier response on the same instance. A test
  asserting "this request is unauthenticated" must not reuse a client that
  already logged in — it must construct a fresh ``ApiHttpClient`` (fresh
  ``httpx.Client``, empty cookie jar), not attempt to clear cookies off a
  used one.
- This wrapper deliberately has no cookie-clearing method: isolation is a
  feature-client/fixture concern (construct a new instance), never something
  this transport layer manages on behalf of callers.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Explicit, fail-fast timeouts (ADR-002): a hung request must not stall a
# rate-budgeted run. No phase is allowed to block indefinitely.
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


def cookie_names(cookies: httpx.Cookies) -> set[str]:
    """Names of cookies in a jar, safe against same-name/different-domain conflicts.

    Observed on the real login response: Matchbook sets *two* ``session-token``
    cookies scoped to different domains (``api.matchbook.com`` and
    ``.matchbook.com``). httpx.Cookies.get()/``__contains__``/``dict()`` all
    raise ``CookieConflict`` in that situation since they can't disambiguate
    by name alone — existence-only checks must go through the jar directly.
    """
    return {cookie.name for cookie in cookies.jar}


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """Evidence-friendly envelope around an httpx response.

    ``raw`` keeps the untouched httpx.Response for callers that need headers,
    cookies, or anything else; ``data``/``elapsed_ms`` exist because every test
    wants parsed JSON and timing, and NFR-5 wants that evidence captured once,
    centrally, rather than recomputed per test.
    """

    status_code: int
    data: Any | None
    raw: httpx.Response
    elapsed_ms: float

    def __str__(self) -> str:
        request = self.raw.request
        body = self.raw.text or ""
        return (
            f"{request.method} {request.url} -> {self.status_code} "
            f"({self.elapsed_ms:.0f} ms)\n{body[:4000]}"
        )

    @property
    def request_headers(self) -> dict[str, str]:
        """The headers actually sent on the wire, including any cookie header
        httpx added from its cookie jar. Exists so tests can assert on real
        outgoing auth state (e.g. "no session-token header or cookie was
        sent") instead of only on the response — see ``ApiHttpClient``'s
        docstring on cookie persistence.
        """
        return dict(self.raw.request.headers)

    @property
    def cookie_names(self) -> set[str]:
        """Names of cookies this specific response set, per ``cookie_names()``."""
        return cookie_names(self.raw.cookies)


class ApiHttpClient:
    """Synchronous httpx.Client wrapper shared by all feature API clients."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
        event_hooks: dict[str, list] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        # event_hooks defaults to empty lists (not None) so callers can attach
        # rate-limiting/evidence-capture hooks later via `.event_hooks["request"].append(...)`
        # without first checking whether the dict was initialized.
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            event_hooks=event_hooks or {"request": [], "response": []},
            headers=headers,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        """The underlying client's cookie jar.

        Read-only introspection, not a way to clear/mutate it mid-test:
        isolation is "construct a new ``ApiHttpClient``", never "reset this
        one's cookies" (see the class docstring's cookie-behavior note). This
        exists so tests can *prove* auth-state isolation between two client
        instances instead of assuming it from the code.
        """
        return self._client.cookies

    @property
    def cookie_names(self) -> set[str]:
        """Names of cookies in this client's jar, per ``cookie_names()``."""
        return cookie_names(self._client.cookies)

    def _request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        start = time.perf_counter()
        response = self._client.request(method, path, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.0f ms)",
            method,
            response.request.url,
            response.status_code,
            elapsed_ms,
        )
        try:
            data: Any | None = response.json()
        except ValueError:
            data = None
        return ApiResponse(
            status_code=response.status_code,
            data=data,
            raw=response,
            elapsed_ms=elapsed_ms,
        )

    def get(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> ApiResponse:
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ApiHttpClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()