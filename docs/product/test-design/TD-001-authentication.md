# TD-001 — Test Design: Login Endpoint

- **Status:** Draft
- **Owner:** QA / SDET (Mykola Mizin)
- **Related docs:** [PRD-001 — Authentication](../prd/PRD-001-authentication.md)

This document describes **how** test cases for the login endpoint are derived and
which of them are automated. Requirements themselves live in PRD-001.

## 1. Techniques used to derive cases

| Technique | Applied to |
|---|---|
| Equivalence partitioning | `username` / `password` value classes (valid, wrong, non-existent, empty, malformed type) |
| Boundary value analysis | Field lengths (empty, minimal, very long), whitespace edges |
| Decision table | Field-presence combinations (username × password: present/missing/null) |
| Error guessing | Invalid JSON, wrong `Content-Type`, wrong HTTP method, injection-style payloads, unicode |
| Use case testing | Full happy path: login → token usable on an authenticated endpoint |

Each derived case is recorded using the project's test-case template with its
technique, partition/boundary covered, and expected result.

## 2. Automation decision framework

Every case gets an explicit decision:

- **AUTOMATE_API** — safe, deterministic, repeatable against the live endpoint
  within the execution constraints (PRD-001 §6). This is the default for positive,
  most negative, and edge cases.
- **MANUAL / one-off observation** — cases that are **destructive to shared state**
  and must not run in regression:
  - Verifying the 3-consecutive-failures account suspension itself (would suspend
    the shared account).
  - Verifying the >25 attempts/minute IP block (would block the runner's IP).
  These are documented with expected behavior and, at most, verified once manually
  in a controlled way.
- **DEFER** — cases requiring capabilities we don't have in blackbox mode (e.g.
  clock manipulation for the ~6 h session expiry) — documented with rationale.

## 3. Lockout-aware sequencing

Design rules that keep the automated suite safe (implementing PRD-001 NFR-1/NFR-2):

1. Negative-credential cases default to **non-existent usernames**, so failures do
   not accrue against the real account.
2. The single "valid user + wrong password" case is one encapsulated unit:
   wrong-password attempt → assert `400` → recovery login → assert `200`.
3. All login calls pass through a shared rate limiter keeping the suite well under
   the 25/minute IP budget — enforced globally across all parallel workers
   (pytest-xdist). Each test declares its isolation category (stateless /
   session-state / account-state, per Architecture Design §4): stateless tests run
   on any worker; session-state tests run with controlled isolation and may run in
   parallel only once independent session behavior is confirmed against the real
   API (we do not assume it supports unlimited concurrent session creation);
   account-state tests execute as atomic, non-interleaving units.
4. If a supposedly valid login fails unexpectedly, the suite aborts fast rather
   than retrying (a retry storm is how accounts get suspended).

## 4. Requirements coverage matrix

Traceability from PRD requirement to planned coverage — every important PRD-001
requirement has designed test coverage, and every planned test traces back to a
requirement:

| Requirement | Technique | Planned coverage |
|---|---|---|
| FR-1.1 Valid credentials | Positive testing (EP: valid class) | Successful login returns `200` + non-empty session token |
| FR-1.2 Response schema | Positive testing | Response matches documented contract (fields, types) |
| FR-1.3 Token usability | Use case testing | Token accepted by an authenticated endpoint |
| FR-1.4 Repeated logins | Use case testing | Consecutive valid logins behave consistently |
| FR-2.1 Non-existent user | Equivalence partitioning | `400`, no token, no user-enumeration hints |
| FR-2.2 Wrong password | Decision table / EP | Invalid credentials handling (atomic account-state unit) |
| FR-2.3 Missing fields | Decision table | username × password present/missing/null combinations |
| FR-2.4 Malformed input | Error guessing | Invalid JSON, wrong types, empty body, wrong `Content-Type` — 4xx, never 5xx |
| FR-2.5 Wrong HTTP method | Error guessing | GET/PUT/DELETE on session URL → 4xx |
| FR-3.1 Boundary/format | Boundary value analysis | Empty, whitespace, case variants, long values, unicode |
| FR-3.2 Injection payloads | Error guessing | Security input validation — clean 4xx, no internals leaked |
| FR-3.3 No password echo | Error guessing | Error bodies never contain the submitted password |
| FR-4.1 Consistency | Repetition (opportunistic) | Identical requests → consistent status/error shape |
| §3.2 Suspension / IP block | Checklist (documented) | Not automated — destructive; documented as manual observation (§2) |

## 5. Test data strategy

Test data is segregated by risk to shared state — the guiding rule is that
**destructive or failure-generating scenarios never touch the real account**,
because its lockout counter is shared, persistent state that one careless test can
poison for the entire suite (and for anyone else using the account).

### Real test account

Used **only** for:

- successful authentication (and token-usability verification);
- the single controlled wrong-password scenario (atomic, with recovery login).

Rationale: account lockout protection and avoiding state pollution — every failed
attempt with the real username spends one of only three strikes.

### Synthetic data

Used for:

- non-existent usernames (the default vehicle for negative-credential cases);
- invalid credential combinations;
- boundary values on username/password fields.

Synthetic identities make failures free: they cannot accrue against any real
account's counter (they still consume the shared IP rate budget, so pacing applies).

### Generated payloads

Used for:

- malformed JSON and structurally invalid bodies;
- unicode and special characters;
- very long strings;
- injection-like inputs.

These are produced systematically (per the §1 techniques) rather than hand-picked,
so the malformed-input space is covered deliberately and reproducibly.

## 6. Next artifact

The Test Case Specification generated from this design lives at
[`test-cases/api/authentication/login.md`](../../../test-cases/api/authentication/login.md)
with automation decisions in
[`login-automation-decisions.md`](../../../test-cases/api/authentication/login-automation-decisions.md).
It contains:

- unique test IDs;
- requirement mapping (extending the §4 matrix to individual cases);
- preconditions;
- test steps;
- expected results;
- automation decision per case (per the §2 framework).