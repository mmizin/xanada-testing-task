# API Test Automation Decision Framework

## Overview

Not every test case should be automated. This framework helps you decide which tests to automate (`AUTOMATE_API` / `AUTOMATE_UNIT`), which to defer (`DEFER_INTEGRATION`), and which require manual inspection (`MANUAL_OBSERVABILITY`).

**Decision Outcomes:**
- **✅ AUTOMATE_API** — Automate in pytest; runs in CI/CD regression suite
- **✅ AUTOMATE_UNIT** — Automate as isolated unit test; runs first in CI/CD
- **⏸ DEFER_INTEGRATION** — Postpone automation; revisit when contract/dependencies stabilize or are mockable
- **🧍 MANUAL_OBSERVABILITY** — Requires manual log/metric inspection or exploratory testing

---

## 8 Scoring Dimensions

For each test case, score 0–5 on each dimension. Then apply decision rules.

### 1. Business Criticality (0–5)
**Impact on revenue, core user workflows, or SLA compliance**

- **5** = Revenue-critical path (e.g., "search offers", "create booking")
- **4** = Core feature, high user visibility (e.g., "user profile update")
- **3** = Important but not critical (e.g., "filter offers by amenities")
- **2** = Nice-to-have feature (e.g., "export search results")
- **1** = Internal tool or edge case
- **0** = Experimental / not yet in production

**Why it matters:** High-criticality tests must be automated to catch regressions fast.

---

### 2. Replaceability (Integration Necessity) (0–5)
**Can this be tested in isolation (unit), or does it need integration?**

- **5** = Requires full integration (database, cache, external APIs, auth)
- **4** = Requires database and some services
- **3** = Requires database OR one external service
- **2** = Requires database, but can mock external services
- **1** = Pure logic, can stub/mock everything
- **0** = No external dependencies, pure function

**Why it matters:** Pure unit tests (0–1) are fast and reliable; integration tests (4–5) are slower, need setup, more brittle.

**If Replaceability ≤ 2:** Consider `AUTOMATE_UNIT` (isolated, no fixtures).
**If Replaceability ≥ 4:** Harder to automate; may be `DEFER_INTEGRATION`.

---

### 3. Stability (0–5)
**Is the API contract stable, or does it change frequently?**

- **5** = Contract fully stable, published, versioned
- **4** = Contract stable, internal agreement in place
- **3** = Contract mostly stable, occasional tweaks
- **2** = Contract evolving, expected changes in next 2–4 weeks
- **1** = Contract unstable, frequent changes
- **0** = No contract defined yet

**Why it matters:** Tests for unstable contracts break constantly, wasting effort.

**If Stability ≤ 2:** Prefer `DEFER_INTEGRATION` until contract settles.

---

### 4. Flakiness Risk (0–5)
**Likelihood of intermittent failures due to timing, async, external volatility**

- **5** = Highly flaky (async operations, external service timeouts, network latency)
- **4** = Moderately flaky (sometimes timeouts, race conditions possible)
- **3** = Occasional timing issues (background jobs, eventual consistency)
- **2** = Low flakiness risk (deterministic, few async calls)
- **1** = Very low flakiness risk (sync, no external services)
- **0** = Zero flakiness (pure logic, no I/O)

**Why it matters:** Flaky tests erode confidence and waste debug time.

**If Flakiness Risk ≥ 4:** Strong signal for `DEFER_INTEGRATION` (wait for mocks/stubs).

---

### 5. Execution Frequency (0–5)
**How often does this test run in CI/CD?**

- **5** = Every commit (smoke suite)
- **4** = Every PR (sanity/quick regression)
- **3** = Every merge to main (full regression)
- **2** = Nightly or on-demand (long-running tests)
- **1** = Weekly or scheduled
- **0** = Never (exploratory only)

**Why it matters:** Tests that run frequently must be fast and stable.

**If Frequency ≥ 4:** Test must be fast (< 1 second) and stable; may exclude slow integration tests.

---

### 6. Maintenance Cost (0–5)
**Effort to keep the test working as code/API evolves**

- **5** = Very high (complex setup, many fixtures, brittle assertions)
- **4** = High (moderate setup, some brittle points)
- **3** = Moderate (standard setup, mostly stable)
- **2** = Low (simple setup, clear assertions)
- **1** = Very low (minimal dependencies, single assertion)
- **0** = Negligible (pure logic, no external deps)

**Why it matters:** High-maintenance tests become liabilities; low-maintenance tests pay for themselves.

**If Maintenance Cost ≥ 4:** Consider if the test is worth automating.

---

### 7. External Dependency Complexity (0–5)
**Complexity of third-party services, auth, mocking**

- **5** = Complex (multiple services, SSO, payment gateway, complex contract)
- **4** = Moderate-high (1–2 services, contract somewhat simple)
- **3** = Moderate (1 service with clear contract, or auth layer)
- **2** = Low (one simple service, can mock easily)
- **1** = Very low (simple auth, one easy-to-mock dependency)
- **0** = No external dependencies

**Why it matters:** High complexity makes automation slow and brittle; mock/stub where possible.

**If External Dependency ≥ 4:** Strong signal for `DEFER_INTEGRATION` until you can mock effectively.

---

### 8. Observability (0–5)
**Can you diagnose failures from assertions alone, or do you need to inspect logs/metrics?**

- **5** = Requires manual log/metric inspection (performance, timing analysis)
- **4** = Diagnosis unclear from assertions; need context
- **3** = Some diagnostic info available, but manual inspection helps
- **2** = Good error messages, mostly clear from assertions
- **1** = Very clear failure reason (schema mismatch, status code, etc.)
- **0** = Trivial (assertion speaks for itself)

**Why it matters:** Poor observability makes debugging automated tests hard; not worth automating.

**If Observability ≥ 4:** Consider `MANUAL_OBSERVABILITY` (log/metric inspection required).

---

## Decision Rules

### Rule 1: AUTOMATE_API (Primary)
**Automate if:**
- Business Criticality ≥ 3
- Stability ≥ 3
- Flakiness Risk ≤ 3
- External Dependency ≤ 3
- Maintenance Cost ≤ 3

**AND none of these are true:**
- Replaceability ≤ 2 (indicates a unit test; see Rule 2)
- Observability ≥ 5 (requires manual inspection)

**Outcome:** Automate as full integration test in pytest. Runs in regression suite.

**Example:**
```
Test: "Create offer with valid data returns 201"
- Business Criticality: 5 (revenue-critical)
- Stability: 4 (contract stable)
- Flakiness Risk: 1 (synchronous, deterministic)
- External Dependency: 2 (database only, no services)
- Maintenance Cost: 2 (simple setup)
→ AUTOMATE_API ✅
```

---

### Rule 2: AUTOMATE_UNIT
**Automate if:**
- Replaceability ≤ 2 (pure logic, no integration)
- Business Criticality ≥ 2
- Stability ≥ 2

**Outcome:** Automate as isolated unit test. Runs first in CI/CD (before integration tests).

**Example:**
```
Test: "Price validator rejects negative amounts"
- Replaceability: 0 (pure function, no external calls)
- Business Criticality: 4 (critical business rule)
- Stability: 5 (contract stable)
→ AUTOMATE_UNIT ✅
```

---

### Rule 3: DEFER_INTEGRATION
**Defer if ANY of these are true:**
- External Dependency ≥ 4 (too complex to mock/stub)
- Flakiness Risk ≥ 4 (too flaky for regular CI/CD)
- Stability ≤ 2 (contract unstable)
- Maintenance Cost ≥ 4 (not worth the effort)
- Observability ≥ 5 (requires manual inspection)

**Outcome:** Postpone automation. Revisit when:
- Dependencies are mockable (add mocks, then automate)
- Contract stabilizes
- Flakiness mitigated (add retry logic, timeouts, stubs)
- Observability improves (better error messages)

**Example:**
```
Test: "Search offers with live external data service"
- External Dependency: 5 (live payment API, timeout-prone)
- Flakiness Risk: 5 (network latency, occasional timeouts)
- Stability: 2 (API contract evolving)
→ DEFER_INTEGRATION ⏸ (Mock the API, then automate)
```

---

### Rule 4: MANUAL_OBSERVABILITY
**Use if:**
- Test requires log/metric inspection to diagnose
- Test is exploratory (no fixed expected result)
- Test involves performance analysis or load scenarios
- Test requires real-world data (production-like environment)

**Outcome:** Document in a runbook or monitoring checklist. Run manually or via observability tool, not CI/CD.

**Example:**
```
Test: "API response time under load stays below 200ms"
- Observability: 5 (requires metrics/APM inspection)
- Execution Frequency: 1 (nightly, not on every commit)
→ MANUAL_OBSERVABILITY 🧍 (Run via load-test tool, inspect APM dashboard)
```

---

## Scoring Examples

### Example 1: POST /api/offers (Create Offer)

| Dimension | Score | Reason |
|---|---|---|
| Business Criticality | 5 | Revenue-critical: users create bookings here |
| Replaceability | 4 | Requires database + auth, but no external services |
| Stability | 5 | Contract frozen, internal agreement |
| Flakiness Risk | 1 | Synchronous, no async operations |
| Execution Frequency | 5 | Part of smoke suite (every commit) |
| Maintenance Cost | 2 | Standard fixture setup, clear assertions |
| External Dependency | 1 | Only database, no third-party services |
| Observability | 1 | Clear assertion: status 201, schema valid |

**Decision: AUTOMATE_API ✅** (all green lights)

---

### Example 2: GET /api/offers/{id} (Fetch Offer with Real-Time Availability)

| Dimension | Score | Reason |
|---|---|---|
| Business Criticality | 4 | Core feature, but availability data from external service |
| Replaceability | 4 | Requires database + external inventory API |
| Stability | 2 | Inventory API contract evolving; frequent schema changes |
| Flakiness Risk | 4 | External service timeouts possible |
| Execution Frequency | 4 | Part of sanity suite |
| Maintenance Cost | 4 | Complex fixture setup (mock availability service) |
| External Dependency | 5 | Inventory API + auth layer |
| Observability | 2 | Clear assertion, but may need API logs to diagnose |

**Decision: DEFER_INTEGRATION ⏸** (Stability ≤ 2, External Dependency ≥ 4, Flakiness Risk ≥ 4)
**Action:** Wait for inventory API contract to stabilize; add comprehensive mocks; revisit in 2 weeks.

---

### Example 3: Validate Price Range (Pure Logic)

| Dimension | Score | Reason |
|---|---|---|
| Business Criticality | 4 | Core business rule (prices must be valid) |
| Replaceability | 0 | Pure function, no dependencies |
| Stability | 5 | Contract frozen (spec: min 0, max 999999) |
| Flakiness Risk | 0 | No external calls |
| Execution Frequency | 5 | Every test that creates/updates offers |
| Maintenance Cost | 1 | Single assertion |
| External Dependency | 0 | None |
| Observability | 0 | Trivial assertion |

**Decision: AUTOMATE_UNIT ✅** (pure logic, no integration needed)

---

## Summary

| Decision | When to Use | Characteristics | CI/CD Stage |
|---|---|---|---|
| **AUTOMATE_API** | Integration tests with stable contracts, low flakiness | Criticality ≥ 3, Stability ≥ 3, Dependencies ≤ 3 | Regression suite |
| **AUTOMATE_UNIT** | Pure logic, no external dependencies | Replaceability ≤ 2, Criticality ≥ 2 | Unit/smoke stage (runs first) |
| **DEFER_INTEGRATION** | Complex/flaky/unstable tests | External Dependency ≥ 4, Flakiness ≥ 4, Stability ≤ 2 | None (revisit later) |
| **MANUAL_OBSERVABILITY** | Exploratory, performance, log-dependent | Observability ≥ 5, or exploratory | Manual/monitoring only |

---

## Tips

- **Start with high-criticality tests:** Automate the smoke suite first (5–10 tests).
- **Build up unit tests gradually:** Use pure-logic tests to establish test infrastructure.
- **Defer flaky tests:** Don't force automation on unreliable tests; fix the flakiness first.
- **Review decisions quarterly:** As contract matures and mocks improve, move tests from DEFER → AUTOMATE.
- **Document why you deferred:** Save the decision (e.g., "Deferred until inventory API stabilizes Q3 2025") so you revisit it.
