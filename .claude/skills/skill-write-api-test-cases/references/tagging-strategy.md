# API Test Tagging Strategy

## Overview

Tags organize tests for execution, reporting, and filtering. Use tags to:
- **Filter test runs** (e.g., `pytest -m "smoke"` runs only smoke tests)
- **Generate reports** (e.g., "75% coverage for @auth tests")
- **Manage CI/CD gates** (e.g., smoke tests on every commit, regression nightly)
- **Track coverage by feature** (e.g., "all @offers tests pass")

---

## Tag Axes

Tags organize along four axes. Each test should have tags from each axis (some are optional).

### Axis 1: Execution Tier (REQUIRED — pick exactly ONE)

Controls **when** and **how often** the test runs.

| Tag | Purpose | When to Use | Example |
|---|---|---|---|
| `@smoke` | Build-breaker tests, run every commit | Critical happy-path, must pass or build is broken | "Create offer returns 201" |
| `@sanity` | Post-deploy validation, quick check | Confirms deployment succeeded, fast subset | "Verify API is responding" |
| `@regression` | Guards existing behavior, full suite | Most tests; catch regressions | Default for all tests |
| `@critical` | Must-pass pre-prod gate | SLA-critical features, can't ship without | "Search offers works", payment processing |

**Rules:**
- Every test must have exactly ONE execution-tier tag
- `@critical` tests also get `@smoke` (they're build-breakers too)
- Smoke suite should be ≤ 10 tests (< 30 seconds total)
- Sanity suite should be ≤ 50 tests (< 5 minutes)

**Pytest Usage:**
```bash
pytest -m smoke                    # Run only smoke tests
pytest -m "smoke or sanity"        # Run smoke + sanity
pytest -m "regression and offers"  # Run offers regression tests
```

---

### Axis 2: Lifecycle / CI Control (OPTIONAL — pick at most ONE)

Controls **exclusions** and **special handling** in CI/CD.

| Tag | Purpose | When to Use |
|---|---|---|
| `@quarantine` | Known flaky, excluded from all gates | Intermittent failures, debugging in progress |
| `@slow` | Long-running, moved to separate CI stage | Tests that take > 10 seconds |
| `@wip` | Work in progress, completely skipped | Feature not yet complete, test not ready |

**Rules:**
- Never combine `@smoke + @quarantine` (if it's build-critical, fix the flakiness)
- `@slow` tests run nightly, not on every commit
- Move tests out of `@quarantine` once fixed

**Pytest Usage:**
```bash
pytest -m "not quarantine"         # Skip flaky tests
pytest -m "smoke and not slow"     # Smoke suite excluding slow tests
```

---

### Axis 3: Test Type (REQUIRED — pick exactly ONE)

Distinguishes **scope** of the test (unit vs. integration vs. contract).

| Tag | Purpose | When to Use | Example |
|---|---|---|---|
| `@unit` | Isolated function/method, no fixtures | Pure logic, no database/external calls | "Price validator rejects negatives" |
| `@integration` | Multi-component flow, touches database/services | Full feature flow, realistic setup | "Create offer, search, update" |
| `@contract` | API contract validation only | Response schema, status code, field types | "POST /offers response schema" |

**Rules:**
- `@unit` tests run first, fastest (no setup)
- `@integration` tests are slower (database, fixtures)
- `@contract` tests validate the interface (no business logic)
- Most tests should be `@integration` (realistic scenarios)

**Pytest Usage:**
```bash
pytest -m unit                     # Run unit tests first
pytest -m integration              # Run integration tests
```

---

### Axis 4: Coverage Type (OPTIONAL — pick one or more)

Specifies **what kind of testing** this is (happy-path, error, security, etc.).

| Tag | Purpose | When to Use |
|---|---|---|
| `@negative` | Invalid input, error response, rejected state | Boundary failures, validation errors, unauthorized access |
| `@boundary` | Boundary value analysis tests | Tests at limits: min-1, min, min+1, max-1, max, max+1 |
| `@security` | Auth, authorization, injection, sensitive-data | Login, token validation, password reset, SQL injection |
| `@performance` | Response time, throughput, load testing | "Response time < 200ms", "Handle 1000 req/sec" |
| `@state-mutation` | Tests that change data (create, update, delete) | POST, PUT, PATCH, DELETE operations |

**Rules:**
- Tests can have multiple coverage tags
- `@negative` tests must also have a clear error-path scenario
- All mutation tests (`@state-mutation`) should clean up after themselves
- Performance tests often run separately (`@slow @performance`)

**Examples:**
- "Delete offer with valid ID" → `@regression @integration @state-mutation @offers`
- "Search with invalid filter type returns 400" → `@regression @integration @negative @validation @search`
- "Verify CSRF token validation" → `@critical @smoke @security @auth`

---

### Axis 5: Feature Area (REQUIRED — pick one or more)

Project-specific tags for your domain. **Extend freely** based on your features.

**Example Features:**
- `@auth` — Authentication and authorization
- `@search` — Search and filtering
- `@users` — User profile and settings
- `@validation` — Input validation rules

**Rules:**
- Every test should have at least ONE feature tag
- A test can span multiple features (tag all relevant)
- Add new tags as features grow
- Use `@validation` for cross-cutting validation tests

---

## Tag Combinations (Examples)

### Happy-Path Test (Most Common)
```
@smoke @integration @offers  (or @regression instead of @smoke)
```
"Create offer returns 201, offer saved in database"

### Error-Path Test
```
@regression @integration @negative @offers
```
"Create offer with missing title returns 400"

### Boundary Test
```
@regression @integration @boundary @offers
```
"Create offer with max-length title (500 chars) succeeds"

### Security Test
```
@critical @smoke @security @auth
```
"Search offers without auth token returns 401"

### Mutation Test (Data Change)
```
@regression @integration @state-mutation @offers
```
"Update offer status from ACTIVE to INACTIVE"

### Unit Test
```
@regression @unit @validation
```
"Price validator accepts 0, rejects -1"

### Slow Performance Test
```
@regression @slow @performance @search
```
"Search 1M offers with complex filter returns < 500ms"

---

## CI/CD Execution Strategy

### Stage 1: Unit Tests (30 seconds, every commit)
```
pytest -m "unit and not quarantine"
```
Fast feedback, pure logic, no flakiness.

### Stage 2: Smoke Tests (< 2 minutes, every commit)
```
pytest -m "smoke and not slow and not quarantine"
```
Build breakers, critical happy-paths only.

### Stage 3: Quick Regression (< 10 minutes, every PR)
```
pytest -m "integration and not slow and not quarantine and not performance"
```
Full integration suite minus slow/performance tests.

### Stage 4: Full Regression (30–60 minutes, after merge)
```
pytest -m "regression and not quarantine"
```
Everything except known flaky tests.

### Stage 5: Nightly / Scheduled (2+ hours, nightly)
```
pytest -m "regression"  (includes @slow, @performance, @quarantine investigations)
```
Full suite plus exploratory/slow tests.

---

## Pytest Configuration

Add markers to `pytest.ini`:

```ini
[pytest]
markers =
    # Execution tiers
    smoke: critical happy-path tests (runs on every commit)
    sanity: post-deploy validation
    regression: regression tests (default)
    critical: must-pass pre-prod gate
    
    # Lifecycle
    quarantine: known flaky, excluded from gates
    slow: long-running tests (> 10 seconds)
    wip: work in progress, skipped
    
    # Test type
    unit: isolated function/method tests
    integration: multi-component tests
    contract: API contract validation
    
    # Coverage type
    negative: invalid input, error paths
    boundary: boundary value tests
    security: auth, authorization, injection
    performance: response time, throughput
    state-mutation: tests that change data
    
    # Feature areas (project-specific)
    offers: offer management features
    search: search and filtering
    likes: user favorites
    auth: authentication/authorization
    bookings: booking creation/management
    payments: payment processing
    users: user profiles
    validation: input validation
```

---

## Reporting & Analysis

### Test Summary by Tag
```bash
# Count tests by tag
pytest --collect-only -q | grep "@offers" | wc -l

# Run and report by feature
pytest -m offers -v --tb=short
```

### Coverage Report
```
Feature Coverage:
  @offers       → 42 tests (12 @unit, 20 @integration, 10 @contract)
  @search       → 38 tests (5 @unit, 25 @integration, 8 @contract)
  @auth         → 15 tests (3 @unit, 8 @integration, 4 @security)
  @validation   → 22 tests (20 @unit, 2 @integration)

CI/CD Gates:
  Smoke suite   → 8 tests (< 30 seconds)
  Sanity suite  → 35 tests (< 5 minutes)
  Regression    → 117 tests (< 20 minutes)
```

---

## Common Mistakes

### ❌ Over-tagging
```
@smoke @sanity @regression @critical @offers @search @negative @boundary
```
Too many tags make filtering impossible. Stick to:
- 1 execution tier
- 0-1 lifecycle tag
- 1 test type
- 0+ coverage types
- 1+ feature areas

**Better:** `@smoke @integration @offers` (3 tags)

### ❌ Confusing `@smoke` with `@sanity`
- `@smoke` = Build-critical, runs **every commit**
- `@sanity` = Post-deploy verification, runs **after release**

If a test is `@smoke`, it must pass or CI/CD blocks all merges.

### ❌ Missing feature tags
Every test should identify which feature(s) it covers. This enables:
- "All @auth tests pass? ✓"
- "Which @search tests are flaky?"

### ❌ Mixing `@unit` with `@integration`
A test is either:
- `@unit` (isolated, no fixtures) — fast, deterministic
- `@integration` (realistic flow, fixtures/database) — slower, more realistic

Not both.

---

## Maintenance

### Quarterly Review
- [ ] Check `@quarantine` tests — move to `@regression` or delete if fixed
- [ ] Review slow tests — split if possible
- [ ] Add new feature tags as product grows
- [ ] Archive old/unused feature tags

### When Adding Features
- Add a new feature tag (e.g., `@new-feature`)
- Tag all new tests with it
- Use for tracking coverage: "Do all @new-feature tests pass?"

### When Deprecating Features
- Move tests to `@wip` or delete
- Document why (feature removed, merged into another feature)
- Remove tag from pytest.ini after tests are deleted