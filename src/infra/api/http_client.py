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