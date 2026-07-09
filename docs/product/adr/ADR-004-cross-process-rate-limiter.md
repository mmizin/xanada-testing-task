# ADR-004 — Cross-process Rate Limiter

- Status: Accepted
- Date: 2026-07-08
- Decision makers: QA / SDET

## Context

The external API blocks the IP after more than 25 login attempts per minute. This
budget is **global per IP**, while pytest-xdist runs tests in multiple worker
*processes*:

```
Worker 1 ──► own in-memory limiter ──►┐
Worker 2 ──► own in-memory limiter ──►├──► one shared IP budget (25/min)
Worker 3 ──► own in-memory limiter ──►┘
```

A conventional in-memory limiter lives inside one process. With N workers, each
would enforce the budget independently, multiplying the effective request rate by
N — the suite would blow the IP limit while every individual limiter reports
"within budget". This failure mode is silent until the IP is blocked.

## Considered options

1. **Per-worker limiter with a divided budget** (e.g. 15/min ÷ N workers each) —
   simple, but wasteful when workers are idle, fragile when worker count changes,
   and wrong if any process outside pytest shares the IP budget.
2. **Single shared limiter across all workers** — one global budget that every
   process draws from through a shared coordination mechanism.

## Decision

Use a **shared cross-process rate limiting mechanism**: the suite requires a
global rate limiter shared across all execution workers, enforced at the HTTP
transport layer so no code path can bypass it.

The concrete coordination mechanism (file-lock token bucket, Redis-based limiter,
or another shared medium) is deliberately **not decided here** — it is an
implementation choice that can change without affecting this decision. The
architectural requirement is only: one budget, all workers, no bypass.

## Consequences

Positive:

- Protects the external system: adding workers never increases pressure on the IP
  budget.
- Makes parallel execution (ADR-003) safe — the safety model does not depend on
  worker count.

Negative:

- Additional synchronization complexity: cross-process coordination is harder to
  build and test than an in-memory counter, and the shared mechanism becomes a
  small serialization point all workers contend on.
- The global budget caps total API throughput regardless of parallelism — an
  accepted, deliberate trade-off.
