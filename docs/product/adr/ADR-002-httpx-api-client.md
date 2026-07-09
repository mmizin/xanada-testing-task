# ADR-002 — HTTP Client Selection (httpx)

- Status: Accepted
- Date: 2026-07-08
- Decision makers: QA / SDET

## Context

The framework needs one HTTP client, wrapped by the infrastructure layer, through
which all API traffic flows. The wrapper must support centralized concerns:
per-request rate limiting, evidence capture for reporting, and strict timeout
control (a hung login request must not stall a rate-budgeted run).

## Considered options

### requests

The de-facto standard, battle-tested, simplest option. Sync-only; no built-in
event-hook mechanism as rich as httpx's; default behavior requires discipline
around timeouts (no timeout unless specified per call).

### httpx

Modern client with a requests-compatible API. First-class timeout configuration
(client-level defaults, fail-fast by design), event hooks on request/response
(natural attachment point for rate limiting and evidence capture), and identical
sync/async APIs if async execution is ever needed.

### aiohttp

Async-only. Our suite is fundamentally rate-limited by the external API, so async
concurrency buys nothing here, while forcing an async programming model onto every
test and fixture — complexity without benefit.

## Decision

Use **httpx** (sync mode).

Honest note: for a suite of this size, `requests` would also work. httpx is chosen
for the ergonomics that match our architecture — client-level timeout defaults and
event hooks where the cross-cutting safety/evidence concerns attach — and for the
free option of async later, not because `requests` is inadequate.

## Consequences

Positive:

- Clean API-client abstraction: rate limiting and evidence capture hook into the
  client centrally, so no test can bypass them.
- Fail-fast timeout behavior by default at the client level.
- Future async support possible without changing the client library.

Negative:

- An additional (less universally known) dependency compared to requests; slightly
  smaller ecosystem of examples.
