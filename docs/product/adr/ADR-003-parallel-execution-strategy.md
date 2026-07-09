# ADR-003 — Parallel Execution Strategy for Stateful API Tests

- Status: Accepted
- Date: 2026-07-08
- Decision makers: QA / SDET

## Context

The regression suite should provide fast feedback, and parallel execution
(pytest-xdist) is a project goal. However, the authentication endpoint carries
external state that naive parallelism would violate:

- **Account lockout rules** — 3 consecutive failed logins suspend the shared
  account; interleaved failures from concurrent tests could trip this.
- **Rate limits** — more than 25 login attempts per minute block the IP; the
  budget is per-IP, not per-worker.
- **Session creation** — successful logins create server-side session state with
  unknown concurrency policies.

The decision is not "which runner to use" but: **how do we achieve parallel
execution while protecting external system state?**

## Considered options

1. **Sequential execution only** — safe but slow, and abandons a project goal;
   run time grows linearly with the suite.
2. **Unrestricted parallelism** — fast but unsafe: workers would race on the
   account failure counter and multiply request rate past the IP budget.
3. **Controlled parallelism via test isolation categories** — parallel by
   default, with per-category execution rules for stateful scenarios.

## Decision

Support **controlled parallel execution** (Option 3). Every test declares an
isolation category, and the execution layer enforces the category's rule:

### Stateless

Examples: invalid/non-existent username, malformed payload, missing fields.
No account mutation — can run freely in parallel on any worker, constrained only
by the global rate budget.

### Session-state

Examples: successful login, token validation.
Create server-side sessions. Require controlled isolation: each test owns its
session lifecycle; parallelism is enabled only once independent session behavior
is confirmed against the real API (we do not assume unlimited concurrent session
creation).

### Account-state

Example: wrong password followed by recovery login.
Mutate the shared account's failure counter. Must execute as an atomic workflow
that no other account-state operation can interleave with; serialized among
themselves via execution grouping.

## Consequences

Positive:

- Faster execution and a regression suite that scales with feature count.
- Safety is enforced structurally (categories + shared controls), not by test
  authors' discipline.

Negative:

- Requires an explicit test isolation strategy and category discipline for every
  new test.
- Depends on a cross-process rate limiter (ADR-004) — a per-worker limiter would
  silently break the safety model.
- Speedup for login-heavy tests is bounded by the shared rate budget; parallelism
  mainly accelerates test overhead and non-login work.
