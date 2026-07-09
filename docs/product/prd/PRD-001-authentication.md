# PRD-001 — Authentication (Login Endpoint) Regression Testing

- **Status:** Draft
- **Owner:** QA / SDET (Mykola Mizin)
- **Related docs:** [Idea Brief](../01-idea-brief.md) ·
  [Test Design — Authentication](../test-design/TD-001-authentication.md)
- **API reference:** https://developers.matchbook.com/reference/login

> Scope of this document: **what** the regression suite must achieve. How the
> requirements are implemented (framework, project structure, fixtures, reporting
> stack) belongs to the architecture docs; how test cases are derived belongs to the
> Test Design document.

## 1. Summary

Deliver an automated **blackbox regression test suite** for the Matchbook login
endpoint. The suite verifies that authentication works correctly for valid
credentials, fails safely and informatively for invalid/malformed input, and behaves
reliably — all while respecting the live system's lockout and rate limits.

## 2. Background

This is the deliverable for an SDET evaluation challenge. Reviewers assess depth of
understanding: test-design rationale, handling of real-world constraints, and overall
quality — not exhaustive coverage. Design reasoning must be visible in the delivered
artifacts.

## 3. System under test

### 3.1 Documented API contract

Guaranteed by the public API reference:

| Aspect | Value |
|---|---|
| Method / URL | `POST https://api.matchbook.com/bpapi/rest/security/session` |
| Request body | JSON: `username` (string, required), `password` (string, required) |
| Success | `200 OK`, response contains a `session-token` |
| Token usage | Subsequent requests send `session-token` as cookie or header |
| Session lifetime | ~6 hours |
| Failure | `400 Bad Request` for invalid credentials / malformed requests |

### 3.2 Observed / assumed behavior (requires empirical validation)

Known from the challenge brief, not from public documentation:

- **Account suspension** after **3 consecutive failed logins** for a real account.
- **IP block** after **more than 25 login attempts per minute**.

Assumed and to be confirmed during exploration:

- Exact error response schemas per failure mode.
- Failed logins with non-existent usernames do not count toward the real account's
  suspension counter (they do count toward the IP limit).

Test credentials: username `***********`, password `***********` (provided for the
challenge; handled per NFR-4).

## 4. Goals

1. Automated regression coverage of the login endpoint: positive, negative, edge.
2. Suite is **safe to run repeatedly** against the live endpoint — never triggers
   account suspension or IP block.
3. Every test case is traceable to a documented design decision (recorded in the
   Test Design document).
4. Test results provide enough evidence to diagnose a failure without re-running.

### Non-goals

- Load, stress, or concurrency testing of the login endpoint.
- Testing other Matchbook endpoints (except a token-validation or logout call used
  as a supporting step).
- Whitebox coverage — no source access.

## 5. Functional requirements

Functional requirements state expected endpoint behavior only; how and how often a
scenario may be exercised against the live system is governed by the execution
constraints in section 6.

### FR-1 Positive scenarios
- **FR-1.1** Valid credentials return `200` with a non-empty `session-token`.
- **FR-1.2** Response schema matches the documented contract (fields, types).
- **FR-1.3** The returned token is actually usable (accepted by an authenticated
  endpoint) — proves login "works", not just "responds".
- **FR-1.4** Repeated valid logins behave consistently (new/valid session each time).

### FR-2 Negative scenarios
- **FR-2.1** Non-existent username + any password → `400`, no token, no user
  enumeration hints in the error body.
- **FR-2.2** Valid username + wrong password → `400`, no token.
- **FR-2.3** Missing `username`, missing `password`, missing both → `400`.
- **FR-2.4** Malformed input: empty body, invalid JSON, wrong field types
  (numbers/objects/arrays), null values, wrong `Content-Type` → `400` (or other
  documented 4xx), never `5xx`.
- **FR-2.5** Wrong HTTP method (GET/PUT/DELETE on the session URL) → 4xx
  (e.g. `405`), never `5xx`.

### FR-3 Edge cases
- **FR-3.1** Boundary/format handling: empty strings, whitespace-padded
  credentials, case-variant username, very long values, unicode.
- **FR-3.2** Injection-style payloads (SQL/JSON special characters) are rejected
  cleanly with a 4xx — no stack traces or internal details leaked.
- **FR-3.3** Error responses never echo the submitted password.

### FR-4 Reliability
- **FR-4.1** Identical requests produce consistent status codes and error shapes
  across the run (checked opportunistically, not by hammering the endpoint).

## 6. Non-functional requirements (execution constraints)

- **NFR-1 Lockout safety:** at most **one** failed attempt against the real account
  (test account) per run — this bounds how FR-2.2 may be exercised — and it is always
  followed by a successful login to reset the consecutive-failure counter. All other
  negative cases use clearly non-existent usernames.
- **NFR-2 Rate safety:** total login attempts stay well under 25/minute — target
  ≤ ~15/minute with pacing between calls. This budget is global: it must hold
  regardless of how many test workers run in parallel.
- **NFR-3 Determinism:** tests are independent and order-safe, except the explicit
  wrong-password → recovery-login pairing, which is encapsulated as one unit.
- **NFR-4 Secrets handling:** credentials are supplied via configuration, not
  hard-coded in tests; no output or report may leak the password.
- **NFR-5 Observability:** each test result carries the evidence needed to diagnose
  a failure (request/response captured, password redacted).

## 7. Assumptions

- The login endpoint remains available and its behavior stable for the duration of
  the challenge.
- The test account is maintained (not suspended/rotated externally).
- The public API documentation is sufficiently accurate to base assertions on;
  discrepancies are recorded when observed.
- At least one authenticated endpoint exists and is accessible for validating the
  session token (FR-1.3).
- Tests run from a single IP; the 25/minute budget is not shared with other
  consumers.

## 8. Success metrics

Acceptance criteria say the project is *complete*; these say it is *successful*:

- The suite executes repeatedly (multiple runs per day) without ever suspending the
  shared account or triggering IP rate limiting.
- A deliberately introduced authentication regression (e.g. changed status code or
  broken token) would be detected by at least one test.
- Any test failure is diagnosable from the generated report alone, without
  re-running the suite.
- Run duration remains practical (minutes, not hours) despite rate pacing.

## 9. Acceptance criteria

- [ ] Suite runs end-to-end against the live endpoint without suspension or IP block.
- [ ] All FR-1…FR-4 scenarios implemented or explicitly deferred with rationale in
      the Test Design document.
- [ ] Test-case design and automation decisions documented and consistent with the
      implemented suite.
- [ ] Reports include request/response evidence with the password redacted.

## 10. Risks & open questions

| Risk / question | Mitigation / plan |
|---|---|
| Actual status codes/error schemas may differ from docs (`400` for everything?) | First exploratory run captures real responses; assertions codified from observed behavior and noted where docs disagree |
| Do failed logins with non-existent usernames count toward the real account's lockout? | Assumed no (section 3.2); verified cautiously during exploration |
| Shared account state (suspension) would block the whole suite | Recovery login after the single wrong-password test; abort-fast guard if a login unexpectedly fails |
| Session buildup from repeated logins | Check whether logout is available/needed; otherwise rely on ~6 h expiry |
| Scope uncertainty | Per challenge instructions, message the provided contact |