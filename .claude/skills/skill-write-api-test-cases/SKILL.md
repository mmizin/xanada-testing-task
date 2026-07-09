---
name: skill-write-api-test-cases
description: "Design API test cases using formal techniques and automation decisions. Produces two output files: test cases and automation decisions (AUTOMATE_API / AUTOMATE_UNIT / DEFER_INTEGRATION / MANUAL_OBSERVABILITY) using a hybrid decision framework. Uses black-box (equivalence partitioning, BVA, decision table, state transition, domain analysis, cause-effect graph, use case, pairwise), white-box (statement/branch/path/condition/loop coverage), and experience-based (error guessing, exploratory, checklist) techniques."
disable-model-invocation: false
---

You are an API test design expert and QA decision architect. Given an API endpoint, feature, or user story in `$ARGUMENTS`, generate thorough test cases using standard test design techniques, then evaluate each for automation and save both the test cases and automation decisions to files.

---

## Quick Reference

| I want to... | See |
|---|---|
| Use Swagger/OpenAPI specs in test design | `references/using-swagger-openapi.md` |
| Learn black-box techniques for APIs | `references/black-box-techniques.md` |
| Learn white-box techniques for APIs | `references/white-box-techniques.md` |
| Learn experience-based techniques | `references/experience-based-techniques.md` |
| Understand test tagging for APIs | `references/tagging-strategy.md` |
| See API test case template & format | `references/test-case-template.md` |
| Understand automation decisions | `references/automation-decision-framework.md` |
| Verify my work & create report | `references/verify-report.md` |

---

## Workflow

### Step 0 — Locate Input

Accept input from `$ARGUMENTS`:
- **API endpoint** (e.g., "POST /api/offers", "GET /api/offers/{id}")
- **Feature spec** (e.g., "offers search feature", "user authentication")
- **User story** (e.g., "As an API consumer, I want to search offers with filters")
- **Swagger/OpenAPI URL** (e.g., a live spec URL) or an environment shorthand configured for your project
- **Endpoint description** with business rules, validation, error cases
- **Directory path** to existing tests/specs
- Or **skip to automation scoring** if test cases already exist

**Swagger Support:**
If a swagger URL or environment shorthand is provided, automatically fetch and parse the OpenAPI spec to:
- Discover endpoint signature, request/response schemas, HTTP methods
- Extract validation rules, required fields, field types, limits
- Identify status codes and error responses
- Understand authentication requirements
- Extract business rules from description fields

### Step 1 — Analyse

**If Swagger/OpenAPI provided:** Fetch and parse the spec to extract:
- Endpoint method, path, parameters
- Request/response schemas (fields, types, required, constraints)
- Status codes and error responses
- Authentication and authorization requirements
- Field validation rules (min/max length, patterns, enums)
- Default values and examples

**Then, read relevant source files, API specs, or existing tests to understand:**
- **HTTP method, path, and endpoint signature**
- **Request contract** — headers, query params, request body, authentication, field constraints
- **Response contract** — status codes, response schema, error responses
- **Business rules and validation** — constraints, limits, allowed values, field dependencies
- **Happy-path and error-path flows** — valid operations and failure modes
- **State transitions** — data persistence, side effects, resource lifecycle
- **External dependencies** — database operations, third-party integrations, auth mechanisms
- **Which values are stable specs** (status codes, limits, error messages, HTTP methods) vs. **unstable test data** (specific IDs, timestamps, generated values) — the latter must never be hardcoded into test cases

### Step 2 — Select & Apply Techniques

Choose techniques based on what you're testing:

**Black-Box** (test input/output without knowing internal code):
- **Equivalence Partitioning** — group request inputs into valid/invalid classes
- **Boundary Value Analysis** — test at limits (min−1, min, min+1, max−1, max, max+1)
- **Decision Table Testing** — test all meaningful combinations of request parameters
- **State Transition Testing** — test valid/invalid resource state paths
- **Domain Analysis Testing** — test correlated parameters together (e.g., offer type + price range)
- **Cause-Effect Graph** — map request conditions and response effects
- **Use Case Testing** — test main/alternative/exception flows through the endpoint
- **Pairwise Testing** — every parameter pair covered at least once

**White-Box** (test internal code structure):
- **Statement Coverage** — every line of code executes at least once
- **Decision/Branch Testing** — every condition true/false branch executes
- **Path Testing** — every linearly independent code path covered
- **Condition Testing** — every atomic condition true and false
- **Loop Coverage** — 0, 1, typical, max, max+1 iterations
- **Exception Coverage** — all error/exception paths triggered

**Experience-Based** (use domain knowledge and defect history):
- **Error Guessing** — target nulls, empty strings, special chars, overflows, negative numbers
- **Exploratory Testing** — time-boxed discovery when requirements incomplete
- **Checklist-Based Testing** — systematic reusable checklist for API testing

See the reference files for detailed rules, examples, and when to use each.

### Step 3 — Assign Tags

Apply tags from the standard tag set — pick one from each axis:

**1. Execution Tier (exactly ONE, required):**
- `@smoke` — critical happy-path, build broken without it, runs on every commit
- `@sanity` — quick post-deploy check, runs after release
- `@regression` — guards existing behaviour (most tests default here)
- `@critical` — must-pass pre-prod gate (critical tests also get `@smoke`)

**2. Lifecycle / CI Control (at most ONE):**
- `@quarantine` — known flaky, excluded from all gates
- `@slow` — long-running, moved to separate CI stage
- `@wip` — work in progress, completely skipped in CI

**3. Test Type (exactly ONE):**
- `@unit` — isolated function/method testing
- `@integration` — multi-component flow, may touch database/external services
- `@contract` — API contract validation (request/response schema)

**4. Coverage Type (one or more):**
- `@negative` — invalid input, rejected state, error response
- `@boundary` — boundary value analysis tests
- `@security` — auth, injection, authorization, sensitive-data handling
- `@performance` — response time, throughput, load testing
- `@state-mutation` — tests that change data (create, update, delete)

**5. Feature Area (one or more, project-specific):**
- `@offers` — offers/accommodations
- `@search` — search and filtering
- `@auth` — authentication/authorization
- `@likes` — user likes/favorites
- (extend with your domain-specific features)

**Rules:**
- BVA tests get `@boundary`
- Invalid input tests get `@negative`
- Mutation tests (POST, PUT, DELETE) get `@state-mutation`
- Security tests get `@security`
- `@critical` tests must also carry `@smoke`

See `references/tagging-strategy.md` for detailed tagging rules and common combinations.

### Step 4 — Create Summary Table (Before Saving)

Create a summary table:

| # | Test Case Name | HTTP Method | Path | Technique | Tags | Expected Status | Response Validation |
|---|---|---|---|---|---|---|---|

**Naming:** Each name must describe the scenario standalone. Use **sentence case**. Examples:
- "Search offers with valid filters returns 200"
- "Search offers with invalid filter type returns 400"
- "Search offers with empty results returns 200 with empty array"

### Step 5 — Save File 1: Test Cases

**Path:**
```
test-cases/api/<feature>.md          # API tests
```

**Format:** Use the test case template from `references/test-case-template.md`. Each file should contain:
1. Header with endpoint, techniques, and coverage type
2. Sequential test cases (TC-001, TC-002, etc.)
3. Separators between tests (----)

Include:
- Unique test case ID
- Sentence-case name (no underscores)
- HTTP method and endpoint
- Tags (3–5 tags per test)
- Technique used
- Pre-conditions (explicit, not assumed)
- Request (method, path, headers, query params, body)
- Expected status code
- Expected response schema/validation
- Test data (concrete values for stable specs; characteristics for unstable data)
- Test Data Setup (only for data-dependent cases — describe the characteristic needed; see `references/test-case-template.md`)

**Before saving, self-check each drafted test case for two recurring problems:**
1. **Hardcoded unstable test data** — scan for specific entity IDs, timestamps, user IDs, or generated values. Replace with a generic description of the needed characteristic (e.g., "a valid offer ID" instead of "offer_id: 1026051"). If a value genuinely can't be generalized, keep it but flag it explicitly in the Step 8 report.
2. **Redundant setup** — check that no step repeats the action that establishes the pre-condition's state.

### Step 6 — Score & Decide Automation Layer

For each test case, score against the 8 dimensions in `references/automation-decision-framework.md`:

1. **Business Criticality** — Revenue/core flow importance
2. **Replaceability (Integration Necessity)** — Can it be tested in isolation (unit) or needs integration?
3. **Stability** — API contract stability, endpoint maturity
4. **Flakiness Risk** — Async operations, external dependencies, timing issues
5. **Execution Frequency** — How often it runs (smoke/regression/nightly)
6. **Maintenance Cost** — Test setup complexity, data dependency
7. **External Dependency Complexity** — Third-party integrations, auth, database
8. **Observability** — Can failure be diagnosed from logs/metrics, or needs manual investigation?

**Score 0–5 each.** Apply decision rules:
- **✅ AUTOMATE_API if:** Business Criticality ≥ 3, Stability ≥ 3, Flakiness Risk ≤ 3, External Dependency ≤ 3, Maintenance Cost ≤ 3
- **✅ AUTOMATE_UNIT if:** Integration Necessity ≤ 2 (pure logic test, no DB/external calls)
- **⏸ DEFER_INTEGRATION if:** External Dependency ≥ 4, Flakiness Risk ≥ 4, or contract unstable
- **🧍 MANUAL_OBSERVABILITY if:** Diagnosis requires manual inspection of logs/metrics, or exploratory testing needed

**Rule:** If uncertain → DEFER_INTEGRATION (revisit once contract stabilizes).

See `references/automation-decision-framework.md` for full framework, examples, and scoring rules.

### Step 7 — Save File 2: Automation Decisions

**Path:** Same directory as test cases file:
```
test-cases/api/<feature>-automation-decisions.md
```

**Format:** Decision table + summary

**Important:** Include a **Tags** column in the decisions table to preserve test case tags for implementers.

```markdown
# <Feature> — Automation Decisions

Generated: [date]

## Decisions

| Test Case | Decision | Tags | Reason |
|---|---|---|---|
| Search offers with valid filters returns 200 | AUTOMATE_API | @smoke @regression @search @contract | Revenue-critical, stable contract, deterministic |
| Search offers with auth failure returns 401 | AUTOMATE_API | @regression @security @auth | Core security gate, must be automated |
| Search with external data service timeout | DEFER_INTEGRATION | @regression @integration | Timing-dependent, flaky without service mock |

## Summary

- **AUTOMATE_API**: X tests (run in CI/CD, regression suite)
- **AUTOMATE_UNIT**: X tests (isolated logic, run first in CI/CD)
- **DEFER_INTEGRATION**: X tests (revisit when contract/dependencies stabilize)
- **MANUAL_OBSERVABILITY**: X tests (require log/metric inspection)
```

### Step 8 — Verify & Report

Before declaring done, verify against `references/verify-report.md`:

**Verification Checklist:**
- [ ] Coverage is complete (happy-path, error-paths, boundary conditions)
- [ ] Tagging is consistent (every test has 1 execution-tier + 1 test-type + 1 feature tag minimum)
- [ ] Naming is clear (sentence case, scenarios standalone)
- [ ] Pre-conditions explicit (not assumed)
- [ ] No hardcoded unstable test data (characteristics/fixtures used instead)
- [ ] Request/response validation concrete (not vague)
- [ ] Status codes documented
- [ ] Response schema/assertions defined
- [ ] Both files created: test cases + decisions

**Report:**
- Total test cases and files created
- Endpoint and HTTP method
- Techniques applied and why
- Tag distribution
- Automation decision breakdown (AUTOMATE_API / AUTOMATE_UNIT / DEFER_INTEGRATION / MANUAL_OBSERVABILITY counts)
- Coverage gaps or assumptions
- Hardcoded data flagged (any values that couldn't be generalized, and why)
- Files created
- Next steps (which skill to call next)

See `references/verify-report.md` for full checklist and sample report template.

---

## Edge Cases

- **If input points to existing test-cases file:** Skip Steps 1–4; go directly to automation scoring (Steps 5–7).
- **If multiple endpoints in one feature:** Generate one test-cases file per endpoint, or one file with endpoints grouped by resource.
- **If all test cases are DEFER_INTEGRATION or MANUAL_OBSERVABILITY:** File 2 still gets created (decision table with those values).
- **Feature-area tags are project-specific:** Document them in tagging reference as "extend freely".

---

## Quality Standards

- **No duplicates** — each test case tests something unique; technique overlap OK
- **No vague names** — use sentence case, not snake_case
- **Concrete data for stable specs** — use real values for business-rule constants (status codes, HTTP methods, error messages)
- **No hardcoded unstable test data** — describe the characteristic needed (e.g., "a valid offer ID"), not a specific ID value
- **No redundant setup** — steps never repeat the action that establishes the pre-condition's state
- **Explicit pre-conditions** — state what must be true before test runs
- **Observable results** — measurable outcomes (status codes, response structure), not vague expectations
- **Technique-driven** — justify test count by techniques used, not arbitrary targets
- **Documented gaps** — call out what you didn't test and why
- **Two output files** — test cases + automation decisions, co-located

---

## Key Constraints

- ✋ **Bias against expensive external dependencies.** If test needs live third-party service, prefer DEFER_INTEGRATION until you can mock/stub it.
- 🚫 **Avoid flaky tests at all cost.** A flaky test is worse than no test.
- 📊 **Automate API tests intentionally.** API tests are cheap to maintain; automate aggressively.
- ❓ **If uncertain → DEFER_INTEGRATION.** Err toward deferring tests that need real external services.
- 🔗 **This gates skill-implement-api-test-automation.** Use decisions from this skill before writing tests.

---

## Next Steps

Once both files are saved (`test-cases/api/<feature>.md` and `test-cases/api/<feature>-automation-decisions.md`):

1. **Review** decisions with team (ensure alignment on business criticality)
2. **For `AUTOMATE_API` decisions** → call `skill-implement-api-test-automation` to scaffold pytest tests
3. **For `AUTOMATE_UNIT` tests** → call skill to scaffold unit tests (isolated, no fixtures)
4. **For `DEFER_INTEGRATION` tests** → revisit when contract stabilizes or dependencies mockable
5. **For `MANUAL_OBSERVABILITY` tests** → document in runbook or monitoring checklist

The test cases and decisions files stay in `test-cases/api/` so they're always available during test implementation.

---

## Examples

### Example Input: "POST /api/login endpoint"
**Output 1:** `test-cases/api/login/login.md` (8–12 test cases)
**Output 2:** `test-cases/api/login/login-automation-decisions.md` (decisions table)

### Example Input: "<Swagger/OpenAPI URL> POST /api/login" (with Swagger)
Fetches the spec, parses it, auto-generates test cases from schema constraints.
**Output 1:** `test-cases/api/login/login.md` (15–20 test cases, including boundary and validation tests from spec)
**Output 2:** `test-cases/api/login/login-automation-decisions.md`

---

## Swagger/OpenAPI Support

Provide a direct spec URL, or an environment shorthand if one is configured for your project.

**The skill will:**
1. Fetch the OpenAPI spec
2. Extract endpoint definition (schema, constraints, status codes, auth)
3. Generate test cases based on field constraints, boundaries, and error cases
4. Add exploratory tests for gaps not covered in spec

See `references/using-swagger-openapi.md` for details.
