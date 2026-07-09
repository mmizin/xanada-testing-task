# Authentication (Login) — Automation Decisions

Generated: 2026-07-08
Source: [login.md](login.md) · Framework: `references/automation-decision-framework.md`

Scoring context applied to all cases: the endpoint is a live production API with a
stable, documented contract (Stability 4–5) and no mockable seam (blackbox), so
AUTOMATE_UNIT is never applicable. Flakiness risk is low for stateless cases
(deterministic responses) and controlled for stateful ones via the isolation
strategy (TD-001 §3). Maintenance cost is low: no test data lifecycle beyond
configuration-supplied credentials.

## Decisions

| Test Case | Decision | Tags | Reason |
|---|---|---|---|
| TC-001 Login with valid credentials returns 200 and a session token | AUTOMATE_API | @smoke @critical @contract @auth | Core happy path; criticality 5, stable contract, deterministic |
| TC-002 Successful login response matches the documented schema | AUTOMATE_API | @regression @contract @auth | Contract guard; cheap, deterministic |
| TC-003 Session token is accepted by an authenticated endpoint | AUTOMATE_API | @smoke @regression @integration @auth | Proves login works end-to-end; criticality 5 |
| TC-004 Repeated valid logins behave consistently | AUTOMATE_API | @regression @auth @integration | Reliability signal; low cost within rate budget |
| TC-005 Non-existent username returns 400 without a token | AUTOMATE_API | @regression @negative @auth | Stateless, synthetic data, zero account risk |
| TC-006 Wrong password then recovery login (atomic) | AUTOMATE_API | @regression @negative @security @auth | Criticality 4; safe only as the designed atomic unit with recovery + abort guard |
| TC-007 Missing username field returns 400 | AUTOMATE_API | @regression @negative @contract @auth | Stateless validation; deterministic |
| TC-008 Missing password field returns 400 | AUTOMATE_API | @regression @negative @contract @auth | Stateless validation; deterministic |
| TC-009 Empty body or null fields returns 400 | AUTOMATE_API | @regression @negative @contract @auth | Stateless validation; deterministic |
| TC-010 Syntactically invalid JSON returns 400 | AUTOMATE_API | @regression @negative @contract @auth | Robustness guard; never-5xx assertion |
| TC-011 Wrong field types returns 400 | AUTOMATE_API | @regression @negative @contract @auth | Robustness guard; deterministic |
| TC-012 Wrong Content-Type is rejected | AUTOMATE_API | @regression @negative @contract @auth | Protocol misuse guard; expected code tightened after first run |
| TC-013 Wrong HTTP methods are rejected | AUTOMATE_API | @regression @negative @contract @auth | Method misuse guard; DELETE excluded (it is logout) |
| TC-014 Empty-string credentials returns 400 | AUTOMATE_API | @regression @negative @boundary @auth | BVA length 0; stateless |
| TC-015 Whitespace-padded credentials do not authenticate | AUTOMATE_API | @regression @negative @boundary @auth | Trimming semantics tested safely on synthetic user |
| TC-016 Very long credential values rejected cleanly | AUTOMATE_API | @regression @negative @boundary @auth | BVA extreme length; also guards availability (no timeout) |
| TC-017 Unicode/special characters handled cleanly | AUTOMATE_API | @regression @negative @boundary @auth | Encoding robustness; stateless |
| TC-018 Injection-style payloads rejected without leaking internals | AUTOMATE_API | @regression @negative @security @auth | Security gate; stateless synthetic input |
| TC-019 Error responses never echo the submitted password | AUTOMATE_API | @regression @security @auth | Shared assertion over existing responses; zero extra rate budget |
| TC-020 Identical invalid requests get consistent responses | AUTOMATE_API | @regression @auth @contract | Reliability observation within budget |
| TC-021 Account suspension after 3 consecutive failures | MANUAL_OBSERVABILITY | @wip @negative @security @auth | Destructive to shared account state; suspends the account the whole suite depends on — documented, verified at most once manually |
| TC-022 IP block after >25 attempts/minute | MANUAL_OBSERVABILITY | @wip @negative @performance @auth | Destructive to shared IP; the suite respects the limit by design instead of testing it |
| TC-023 Session token expires after ~6 hours | DEFER_INTEGRATION | @wip @auth @integration | Not verifiable in blackbox regression (no time control; 6 h wait impractical); revisit as a nightly long-running check |

## Summary

- **AUTOMATE_API**: 20 tests (regression suite; 3 also in @smoke, 1 @critical)
- **AUTOMATE_UNIT**: 0 tests (blackbox — no isolated logic seam exists)
- **DEFER_INTEGRATION**: 1 test (session expiry — needs a practical verification path)
- **MANUAL_OBSERVABILITY**: 2 tests (suspension, IP block — destructive to shared state by definition)

## Notes for implementation

- Isolation categories from the test cases are binding: TC-006 must run in the
  account-state execution group; session-state cases (TC-001–TC-004) require
  controlled isolation per ADR-003; all others schedule freely.
- All AUTOMATE_API cases draw on the shared cross-process rate budget (ADR-004);
  several cases have multiple request variants — the total per-run request count
  should be tallied against the ≤ ~15/min target before enabling full parallelism.
- Expected status codes marked "or documented 4xx" are to be tightened to exact
  values after the first verified run, with any doc/behavior mismatch recorded in
  PRD-001 §10.
