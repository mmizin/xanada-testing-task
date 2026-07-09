# Verification & Report Template

Before declaring test design done, verify against this checklist. Then generate a report summarizing your work.

---

## Verification Checklist

Run through this checklist for every test case before saving:

### Content Quality
- [ ] **Test names are clear and descriptive** — describe the scenario standalone, use sentence case (not snake_case)
  - ✅ "Create offer with valid data returns 201"
  - ❌ "test_create_offer" or "TC-001"
  
- [ ] **Pre-conditions are explicit** — don't assume state, state what must be true
  - ✅ "User authenticated with valid token"
  - ❌ "User is logged in" (too vague)

- [ ] **Request is fully specified** — HTTP method, path, headers, params, body all documented
  - ✅ Method: POST, Path: /api/offers, Body: { title: "...", price: 150 }
  - ❌ "Create offer" (vague)

- [ ] **Expected response is measurable** — status code, schema, specific assertions
  - ✅ "Status 201, response contains id UUID, price equals request price"
  - ❌ "Response is correct" (vague)

- [ ] **Test data is concrete for stable specs** — use real values for business rules
  - ✅ Status codes: 200, 201, 400, 401, 404, 409
  - ✅ HTTP methods: GET, POST, PUT, PATCH, DELETE
  - ✅ Error messages: "Email already exists", "Unauthorized"

- [ ] **No hardcoded unstable test data** — use characteristic descriptions instead
  - ✅ "A valid offer ID" (resolved from fixture)
  - ❌ "offer_id: 1026051" (hardcoded production ID)
  
  - ✅ "A user with 'offer:create' permission" (resolved from fixture)
  - ❌ "user_id: 42" (hardcoded)

- [ ] **No redundant setup** — steps don't repeat pre-condition actions
  - ✅ Pre-condition: "User authenticated", Request: POST /api/offers (don't repeat auth in steps)
  - ❌ Pre-condition: "User authenticated", Step 1: "Authenticate user"

### Coverage Verification
- [ ] **Happy-path tested** — main success scenario exists (e.g., "Create offer returns 201")
- [ ] **Error paths tested** — each error code has a test (400, 401, 403, 404, 409, 422, etc.)
- [ ] **Boundary cases tested** — limits and edges covered (min−1, min, max, max+1)
- [ ] **Invalid inputs tested** — type errors, missing fields, invalid enums
- [ ] **State changes tested** — if resource has lifecycle, test transitions
- [ ] **Concurrency tested** — if applicable, race conditions, simultaneous requests
- [ ] **Edge cases covered** — nulls, empty arrays, special characters, unicode

### Tagging Verification
- [ ] **Every test has exactly ONE execution-tier tag** — @smoke, @sanity, @regression, or @critical
- [ ] **Every test has exactly ONE test-type tag** — @unit, @integration, or @contract
- [ ] **Every test has at least ONE feature tag** — @offers, @search, @auth, etc.
- [ ] **Tagging is consistent** — same scenario gets same tags across tests
- [ ] **@critical tests also have @smoke** — critical tests are build-breakers
- [ ] **@smoke suite is small** — <= 10 tests, < 30 seconds total
- [ ] **Coverage tags are used** — @negative, @boundary, @security where applicable

### Automation Decision Verification
- [ ] **Each test has a decision** — AUTOMATE_API, AUTOMATE_UNIT, DEFER_INTEGRATION, or MANUAL_OBSERVABILITY
- [ ] **Decision rationale documented** — why did you choose this decision?
- [ ] **Decisions align with business priority** — high-criticality tests are automated
- [ ] **Flaky tests deferred** — not forced into AUTOMATE_API
- [ ] **Unit tests isolated** — no database/external dependencies (AUTOMATE_UNIT)
- [ ] **Integration tests realistic** — test real workflows with fixtures

### Output Files
- [ ] **Test cases file created** — `test-cases/api/<feature>.md` with all test cases
- [ ] **Decisions file created** — `test-cases/api/<feature>-automation-decisions.md` with decision table
- [ ] **Both files are co-located** — same directory, related names
- [ ] **Files are properly formatted** — markdown, clear structure, readable

---

## Report Template

Generate this report after verification:

```
# <Feature> — Test Design Report

**Endpoint:** `<HTTP_METHOD> <path>` (e.g., `POST /api/offers`)
**Generated:** YYYY-MM-DD
**Designer:** [Your name or "Claude"]

---

## Summary

- **Total Test Cases:** X
- **Test Case Files:** 1 (test-cases/api/<feature>.md)
- **Automation Decisions File:** 1 (test-cases/api/<feature>-automation-decisions.md)

---

## Techniques Applied

| Technique | Count | Reasoning |
|---|---|---|
| Equivalence Partitioning | X | Testing valid/invalid input classes (title, price, status) |
| Boundary Value Analysis | X | Testing numeric limits (price: -1, 0, 1, 999999, 1000000) |
| Decision Table | X | Testing auth × permission × valid_body combinations |
| State Transition | X | Testing offer lifecycle (DRAFT → ACTIVE → INACTIVE) |
| Domain Analysis | X | Testing correlated inputs (check_in + check_out dates) |
| Use Case Testing | X | Testing multi-step workflows (search → select → book) |
| Error Guessing | X | Testing edge cases (nulls, empty, special chars, injection) |

---

## Coverage Analysis

### By Execution Tier
| Tier | Count | Purpose |
|---|---|---|
| @smoke | X | Build-critical, runs every commit |
| @sanity | X | Post-deploy validation |
| @regression | X | Guards existing behavior |
| @critical | X | Must-pass pre-prod gate |

**Smoke suite:** X tests, ~Y seconds total

### By Test Type
| Type | Count | Purpose |
|---|---|---|
| @unit | X | Isolated logic, no dependencies |
| @integration | X | Multi-component flow, realistic setup |
| @contract | X | API contract validation |

### By Feature Area
| Feature | Count | Status |
|---|---|---|
| @offers | X | Y% coverage |
| @search | X | Y% coverage |
| @auth | X | Y% coverage |

### Coverage Type Distribution
| Type | Count | Examples |
|---|---|---|
| Happy-path | X | "Create returns 201", "Search returns results" |
| Error-path (@negative) | X | "Missing field returns 400", "Auth failure returns 401" |
| Boundary (@boundary) | X | "Price at limits: -1, 0, 1, max" |
| Security (@security) | X | "Unauthorized returns 401", "Insufficient permission returns 403" |
| Mutation (@state-mutation) | X | "Update, delete operations" |

---

## Automation Decisions Breakdown

| Decision | Count | Rationale |
|---|---|---|
| AUTOMATE_API | X | Stable contracts, low flakiness, critical features → auto in CI/CD |
| AUTOMATE_UNIT | X | Pure logic, no dependencies → auto in unit test stage |
| DEFER_INTEGRATION | X | External dependencies, unstable contracts → revisit when ready |
| MANUAL_OBSERVABILITY | X | Requires log/metric inspection → run manually |

**Status:** X% automated (X tests automated, Y deferred)

---

## Coverage Gaps & Assumptions

### What's Tested
- ✅ Happy path (create offer, returns 201)
- ✅ Error paths (missing fields, invalid types, auth failures)
- ✅ Boundary conditions (price limits, string length)
- ✅ State transitions (offer status lifecycle)
- ✅ Data persistence (verify database state)

### What's NOT Tested (Intentional)
- ❌ Performance / load testing (deferred to performance test suite)
- ❌ Concurrent updates under high load (deferred, marked @slow)
- ❌ Third-party payment service integration (deferred, mock instead)
- ❌ Email notifications (deferred, out of scope for API tests)

### Assumptions
- Database is available and clean for each test (handled by fixtures)
- Auth service is working (mocked/stubbed)
- External APIs are available or mocked (mocked for integration tests)
- No system clock skew during testing

---

## Hardcoded Data Flagged

(List any values that couldn't be generalized and why)

```
Test Case: "TC-042: Search offers with specific city returns results"
  Hardcoded: city_id = "c_paris_001" 
  Reason: City ID is stable spec (not production data), OK to hardcode
  Alternative: Could use fixture to look up city by name, but hardcoding is simpler

Test Case: "TC-015: Create offer with max-length title"
  Hardcoded: title = "a" * 500
  Reason: Testing boundary, not production data; OK to hardcode
```

*None flagged as problematic.*

---

## Next Steps

1. **Review** — Team review of test cases and decisions (10 min)
2. **Approve** — Get sign-off on business-critical test priorities
3. **Implement** — Call `skill-implement-api-test-automation` to scaffold pytest tests
4. **Execute** — Run test suite, measure coverage
5. **Refine** — Update checklist based on lessons learned

---

## Sample Metrics

(Fill in actual numbers after tests are automated)

```
Metrics:
- Test execution time: X seconds (target: < 2 min for smoke)
- Pass rate: Y% (target: 100%)
- Coverage: Z% statement coverage (target: > 80%)
- Flakiness: A% (target: 0%)
- Review time: B hours

Trends:
- First run: X failures (now fixed)
- Regression: Y bugs found by test suite since creation
- Maintenance: Average Z minutes per quarter to maintain tests
```

---

## Files Generated

```
test-cases/api/<feature>.md
test-cases/api/<feature>-automation-decisions.md
```

**Total size:** X KB, Y lines of markdown

---

## Notes

[Any additional context, decisions, or observations]

Example:
```
- Deferred payment API tests until we can mock Stripe
- Added @slow tag to tests that query 1M+ offers (move to nightly)
- Documented authorization rule: "owner or admin can update offer"
  → Added 4 tests to verify all combinations
- Found edge case: search with min_price > max_price returns confusing error
  → Added validation in API, added test for it
```

---

```

## Quick Reference for Report Completion

**Metrics to Calculate:**

| Metric | How to Calculate | Example |
|---|---|---|
| Total Tests | Sum all test cases | 42 tests |
| Smoke Suite | Count @smoke tests | 8 tests |
| Coverage % | (tests / endpoint paths) × 100 | 95% coverage |
| Automated % | (AUTOMATE / total) × 100 | 85% automated |
| Deferred % | (DEFER / total) × 100 | 15% deferred |

**Tips:**

1. **Keep it concise** — 1–2 pages max. Details go in test case files.
2. **Highlight decisions** — Why you chose AUTOMATE vs. DEFER for key tests.
3. **Flag risks** — Any deferred tests that might need revisiting soon.
4. **Use tables** — Easier to scan than paragraphs.
5. **Include examples** — Help team understand the test design approach.

**Before Submitting:**

- [ ] Report is readable (no jargon, clear to non-technical stakeholder)
- [ ] Numbers add up (test counts, percentages)
- [ ] Files are saved in correct location (test-cases/api/)
- [ ] No spelling/grammar errors
- [ ] Summary is accurate (re-read to verify)
