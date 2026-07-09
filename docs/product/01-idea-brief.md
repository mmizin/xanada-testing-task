# Idea Brief — Login Endpoint Regression Test Suite

## What we are building

A Python-based **blackbox regression test suite** for the Matchbook **login endpoint**.
This is the deliverable for a QA Automation Challenge (SDET position): an automated
suite that exercises the real, live endpoint and demonstrates how it behaves under
positive, negative, and edge-case conditions — and whether it does so reliably.

## Why (context and goals)

This is an evaluation exercise. A "perfect" or exhaustive solution is **not** the goal.
The reviewers are looking for cues that reveal **depth of understanding**:

- Deliberate test design (formal techniques, clear coverage rationale).
- Awareness of real-world constraints (rate limits, account lockout) and how they
  shape test strategy.
- Readable, well-structured code with **comments explaining the intent** behind test
  cases and design choices — the thought process must be visible.

## System under test

- **Endpoint:** Matchbook login API
- **Documentation:** https://developers.matchbook.com/reference/login
- **Access:** real production-like environment, blackbox only (no source access, no
  test hooks, no reset endpoints known).
- **Test credentials:**
  - Username: `***********`
  - Password: `***********`

## Scope

### In scope
- **Positive scenarios:** valid login (token/session returned, response schema,
  status codes, headers).
- **Negative scenarios:** invalid credentials, missing fields, malformed input
  (wrong types, empty body, invalid JSON, oversized payloads), wrong content type,
  wrong HTTP method.
- **Edge cases:** boundary values, whitespace/case handling, unicode and injection-style
  input, idempotency/repeat-login behavior.
- **Reliability observations:** consistency of responses across repeated calls,
  meaningful error messages, no sensitive-data leakage in error responses.

### Out of scope
- Load/stress testing (explicitly dangerous given IP-block limits).
- Other Matchbook endpoints (except logout, if needed for session hygiene).
- Whitebox/unit testing — we have no access to internals.

## Critical operational constraints (⚠️ these drive the design)

The real system enforces limits that can **break test runs or burn the test account**:

1. **Account suspension:** the account is suspended after **3 consecutive failed
   logins**. Design consequences:
   - Never chain multiple wrong-password attempts against the real account.
   - Use clearly-invalid / non-existent usernames for most negative tests so
     failures don't count against the test account.
   - Isolate the single "valid user + wrong password" case and follow it with a
     successful login to reset the failure counter.
2. **IP block:** the IP is blocked after **more than 25 login attempts per minute**.
   Design consequences:
   - Global request pacing/throttling across the whole suite (e.g. a fixture that
     rate-limits every login call).
   - Keep the total suite footprint small and deterministic; no parallel login storms.

These constraints are a feature of the exercise: handling them well is part of what
is being evaluated.

## Solution shape

- **Language/stack:** Python, `pytest`, `requests` (HTTP client wrapper in `src/`),
  Allure for reporting.
- **Layout:**
  - `src/` — API client, fixtures, infra (rate limiter, config), test data, utils.
  - `tests/` — the test suite itself.
  - `docs/` — product/design documentation (this brief, test-case designs).
- **Test design process:** derive test cases with formal techniques (equivalence
  partitioning, BVA, error guessing, etc.), document them, then automate with an
  explicit automate/defer decision per case.

## Success criteria

- Suite runs green (or with clearly-explained expected failures) against the real
  endpoint without triggering account suspension or IP block.
- Coverage of positive, negative, and edge scenarios is traceable to documented
  test-case design.
- Code and comments make the reasoning behind every design choice obvious to a
  reviewer.

## Open questions

- Exact response schema/status codes for each failure mode (to be confirmed against
  the live endpoint and the public docs).
- Whether a session/logout call is required to avoid session buildup between tests.
- For scope or approach uncertainties, the challenge instructions say to message the
  provided contact.