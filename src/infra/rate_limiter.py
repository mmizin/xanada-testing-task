"""Cross-process rate limiter enforcing the shared request budget (ADR-004).

The external API blocks the IP after more than 25 login attempts per minute,
and — as observed against the live API — a stricter Cloudflare burst
protection layer can trigger well under that count if requests arrive too
close together (20 requests in ~4 seconds was enough, despite being far
under 25/minute by count alone). A per-minute counter that lets a whole
budget through at once wouldn't fix that; enforcing a **minimum spacing**
between requests fixes both the burst problem and the per-minute budget with
one mechanism: spacing requests 60/N seconds apart caps the sustained rate at
N/minute *and* guarantees no burst.

Per ADR-004, the budget is global per IP while pytest-xdist runs multiple
worker processes — an in-memory limiter inside one process can't coordinate
with the others. State therefore lives in a file on disk (one line: the
timestamp of the last permitted request), guarded by the same
``filelock.FileLock`` mechanism already used for cross-worker settings
caching in ``conftest.py``. Every worker's ``acquire()`` reads-waits-writes
under the same lock, so the effective rate is shared no matter how many
processes call it.
"""

from __future__ import annotations

import hashlib
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import httpx
from filelock import FileLock


class CrossProcessRateLimiter:
    """Blocks callers, if needed, so requests sharing ``key`` stay spaced
    at least ``60 / max_per_minute`` seconds apart, coordinated across
    processes via a state file on disk.
    """

    def __init__(
        self,
        key: str,
        max_per_minute: float,
        state_dir: Path | str | None = None,
    ) -> None:
        if max_per_minute <= 0:
            raise ValueError(f"max_per_minute must be positive, got {max_per_minute}")
        self._min_interval_seconds = 60.0 / max_per_minute

        # Use digest as filename to avoid filesystem safety issues.
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        base_dir = Path(state_dir) if state_dir is not None else Path(tempfile.gettempdir())
        self._state_path = base_dir / f"matchbook-rate-limiter-{digest}.state"
        self._lock = FileLock(str(self._state_path) + ".lock")

    def acquire(self) -> None:
        """Block until issuing a request now would respect the shared spacing."""
        with self._lock:
            now = time.time()
            earliest_allowed = self._last_request_time() + self._min_interval_seconds
            if now < earliest_allowed:
                time.sleep(earliest_allowed - now)
                now = earliest_allowed
            self._state_path.write_text(repr(now))

    def _last_request_time(self) -> float:
        try:
            return float(self._state_path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return 0.0


def as_request_hook(
    limiter: CrossProcessRateLimiter | None,
) -> list[Callable[[httpx.Request], None]]:
    """Adapt a limiter into an httpx ``event_hooks["request"]`` list.

    Returns an empty list when rate limiting is disabled (``limiter is
    None``), so callers can splice this straight into an ``event_hooks``
    dict without a branch at each call site — the "disabled" mode is simply
    "no hook attached," not a limiter that's built but always permits.
    """
    if limiter is None:
        return []
    return [lambda request: limiter.acquire()]
