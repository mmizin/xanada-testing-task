# Experience-Based Testing Techniques for APIs

Experience-based testing uses domain knowledge, past bugs, and intuition to find bugs that formal techniques might miss.

---

## 1. Error Guessing

**Idea:** Guess where bugs are likely to hide based on common patterns.

**Common error-prone inputs:**

### Null / Empty / Falsy Values
- `null` in request body
- Empty string `""`
- Empty array `[]`
- `0` (number, often treated as falsy)
- `false` (boolean)

**Example: Test "title" field**
```
- TC-001: title = null → 400 or error
- TC-002: title = "" → 400 or error
- TC-003: title = " " (whitespace) → 400 or error
- TC-004: title = false → 400 (wrong type)
```

### Special Characters & Encoding
- Unicode: emoji 🏨, accents (café), CJK (中文)
- SQL injection: `'; DROP TABLE--`, `1 OR 1=1`
- XSS injection: `<script>alert('x')</script>`
- JSON escapes: quotes `"`, backslash `\`, newlines `\n`
- Control characters: null byte `\x00`, tab `\t`

**Example: Test "title" field**
```
- TC-005: title = "Café ☕ Apartment" → 201 (emoji + accents OK)
- TC-006: title = "'; DROP TABLE--" → 201 (stored as literal, not executed)
- TC-007: title = "<script>alert('x')</script>" → 201 (stored as literal, not XSS)
- TC-008: title = "Line 1\nLine 2" → 201 (newlines OK)
```

### Numeric Edge Cases
- Negative numbers: `-1`, `-999999`
- Zero: `0`, `0.0`
- Decimals: `0.01`, `3.14159`
- Very large numbers: `999999999999`
- Precision loss: `0.1 + 0.2 ≠ 0.3` (floating point)
- NaN, Infinity (if applicable)

**Example: Test "price" field**
```
- TC-009: price = 0 → 201 (free offer OK?)
- TC-010: price = 0.01 → 201 (minimum price)
- TC-011: price = 999999.99 → 201 (maximum price)
- TC-012: price = 1000000 → 400 (exceeds max)
- TC-013: price = -1 → 400 (negative)
```

### String Length & Overflow
- Empty: `""`
- Very long: 1000+ chars, exceeds column limit
- Max length: if limit is 500, test 499, 500, 501

**Example: Test "title" field (max 500 chars)**
```
- TC-014: title = "" → 400
- TC-015: title = "a" * 499 → 201 (just under limit)
- TC-016: title = "a" * 500 → 201 (at limit)
- TC-017: title = "a" * 501 → 400 (exceeds limit)
```

### Arrays & Collections
- Empty: `[]`
- Single item: `[1]`
- Duplicates: `[1, 1, 2, 2]`
- Out of order: unsorted array when sorted order expected
- Large collections: 1000+ items

**Example: Test "amenities" field (array)**
```
- TC-018: amenities = [] → 201 (no amenities OK)
- TC-019: amenities = ["WIFI"] → 201 (single amenity)
- TC-020: amenities = ["WIFI", "WIFI"] → 200 or 400? (duplicates handled?)
- TC-021: amenities = ["UNKNOWN"] → 400 (invalid amenity)
```

### Enums & Fixed Sets
- Valid values only: test each value
- Invalid values: test non-existent enum
- Case sensitivity: "ACTIVE" vs "active" vs "Active"
- Whitespace: "ACTIVE " (trailing space)

**Example: Test "status" field (enum: ACTIVE, INACTIVE, PENDING)**
```
- TC-022: status = "ACTIVE" → 201 (valid)
- TC-023: status = "active" → 400 (lowercase invalid)
- TC-024: status = "ACTIVE " → 400 (trailing space)
- TC-025: status = "UNKNOWN" → 400 (invalid enum)
- TC-026: status = null → 400 (required field)
```

### Authentication & Authorization
- Missing auth header: no Authorization header
- Invalid token: expired, malformed, revoked
- Wrong scope: token valid but lacks permission
- Rate limiting: many requests quickly

**Example: Test auth**
```
- TC-027: No Authorization header → 401 (unauthorized)
- TC-028: Authorization = "invalid" → 401 (malformed token)
- TC-029: Authorization = expired token → 401 (expired)
- TC-030: Authorization = valid token with no 'offer:create' scope → 403 (forbidden)
- TC-031: 100 requests in 1 second → 429 (rate limited)
```

### Timestamps & Dates
- Current time: `now()`
- Past: `2020-01-01`
- Future: `2099-12-31`
- Invalid date: `2025-13-45`
- Timezone: UTC vs. local time
- Daylight saving transitions

**Example: Test "check_in" date**
```
- TC-032: check_in = today → 201 (today OK)
- TC-033: check_in = yesterday → 400 (past date)
- TC-034: check_in = 2025-13-45 → 400 (invalid date)
```

### Floating Point Precision
- Rounding: `0.1 + 0.2` should equal `0.3`, but doesn't exactly
- Comparison: use delta/tolerance, not exact equality

**Example: Test price rounding**
```
- TC-035: price = 100.001 → round to 100.00?
- TC-036: Ensure price ± 0.01 is within tolerance for comparison
```

---

## 2. Exploratory Testing

**Idea:** Spend time exploring the endpoint without a fixed test plan. Use intuition and curiosity to find edge cases.

**How to use:**
1. Set a time box (30 minutes, 1 hour)
2. Interact with the endpoint without a predetermined test case
3. Try unusual combinations, rapid changes, stress scenarios
4. Document interesting findings

**Example Exploratory Session: Search Offers**

```
Time box: 30 minutes

Exploration notes:
- "What if I search with no filters?" → 200 with all offers (good)
- "What if I search with conflicting filters?" 
  (min_price > max_price) → Did API handle it gracefully?
- "What if I spam the same search 1000 times?" → Rate limiting?
- "What if I search at exactly midnight?" → State change?
- "What if database is updated during search?" → Stale results?
- "What if I use very large filter values?" → Integer overflow?
- "What if I use non-UTF8 characters in search?" → Encoding error?
- "What if I switch languages mid-search?" → Partial state?
- "What if results are huge (100k items)?" → Memory/timeout?
- "What if I cancel request mid-stream?" → Partial response?

Findings:
- [BUG] Search with min_price > max_price returns confusing error
  → Add validation in API
- [OK] Rate limiting works at 100 req/sec
- [EDGE CASE] Very large filter values cause timeout, should add limit check
- [FEATURE REQUEST] Could warn user when search would return > 1000 results
```

**When to use:**
- New endpoints (unstable, requirements unclear)
- High-risk features (payment, auth)
- After deployment (manual exploratory testing)
- When formal techniques seem incomplete

---

## 3. Checklist-Based Testing

**Idea:** Use a reusable checklist of common API scenarios to test systematically.

**Generic API Checklist:**

```
□ Happy Path
  □ Create resource with all required fields → 201 or 200
  □ Resource created in database with correct values
  □ Response includes all expected fields
  □ Response includes ID / timestamp / created_at

□ Required Fields
  □ Missing each required field one at a time → 400
  □ Error message identifies which field is missing
  □ No resource created in database

□ Field Validation
  □ String too long → 400
  □ String empty → 400
  □ String with special chars → 201 or error (consistent)
  □ Number negative → 400 (if not allowed)
  □ Number exceeds max → 400
  □ Enum value invalid → 400
  □ Email invalid format → 400
  □ Date invalid format → 400

□ Authentication
  □ No auth header → 401
  □ Invalid token → 401
  □ Expired token → 401 (if applicable)
  □ Token without required scope → 403

□ Authorization
  □ User lacks permission → 403
  □ User can't access other user's resource → 403 or 404

□ Idempotency
  □ Same request twice (for PUT/PATCH) → 200, same result
  □ Concurrent requests → no race conditions, consistent state

□ Error Handling
  □ Dependency unavailable (DB down) → 503 or 500
  □ Invalid state → 400 or 409 (depending on case)
  □ Resource not found → 404
  □ Resource already exists → 409 (for create, if not allowed)
  □ Conflict → 409 (version mismatch, state conflict)

□ Response Format
  □ Response status code is correct
  □ Response headers are correct (Content-Type, etc.)
  □ Response body is valid JSON
  □ Response body matches schema
  □ No sensitive data in response (passwords, tokens)

□ Pagination (if applicable)
  □ Default page size returns correct count
  □ Page 1, 2, 3... each returns different results
  □ Last page correctly marked
  □ Requesting page beyond range → 400 or 200 empty?
  □ Large page_size parameter → capped or error?

□ Filtering & Search (if applicable)
  □ Filter by each field works independently
  □ Multiple filters work together (AND logic)
  □ Invalid filter value → 400
  □ No results → 200 with empty array
  □ Case-sensitive / case-insensitive filtering?

□ Sorting (if applicable)
  □ Sort by each field ascending
  □ Sort by each field descending
  □ Invalid sort field → 400 or ignored?
  □ Sort stability (same values maintain order)

□ Rate Limiting (if applicable)
  □ Normal requests pass
  □ Exceeding limit → 429 Too Many Requests
  □ Reset after timeout
  □ Rate limit headers present (X-RateLimit-*)

□ Concurrency
  □ Same user, two simultaneous requests → consistent state
  □ Two users modifying same resource → last-write-wins or error?
  □ Optimistic locking / version conflicts → 409

□ Data Persistence
  □ Resource visible in GET after POST
  □ Resource updated in GET after PUT
  □ Resource removed in GET after DELETE
  □ Database reflects API changes (no lag)

□ Backward Compatibility
  □ Old API version still works (if versioned)
  □ Deprecated fields still accepted
  □ New required fields have defaults
```

**Feature-Specific Checklists:**

**For Payment/Billing APIs:**
```
□ Amount validation
  □ Zero amount → 400?
  □ Negative amount → 400
  □ Non-integer (cents) → accepted or rounded?
  □ Very large amount → 400 or business limit?

□ Currency
  □ Valid currency codes (USD, EUR) → accepted
  □ Invalid currency → 400
  □ Currency conversion (if applicable) → correct rate

□ Payment processing
  □ Successful payment → 201, money deducted
  □ Failed payment → 402 or 422, money NOT deducted
  □ Retry on network error → idempotent?
  □ Double-charge prevention (duplicate request)
```

**For Search/Filter APIs:**
```
□ Query parsing
  □ Simple query → results
  □ Complex query (AND, OR) → correct logic
  □ Malformed query → 400 or ignored?

□ Field coverage
  □ Each searchable field works
  □ Non-searchable field → 400 or ignored?

□ Result accuracy
  □ All returned results match query
  □ No false positives
  □ No false negatives (all matches returned)

□ Performance
  □ Search 1000 items → < 1 second
  □ Search 1M items → timeout or results?
```

**When to use:** Systematic testing of all APIs (not just new ones).

---

## Tips

- **Error guessing finds most bugs:** Spend 50% of test effort on boundary/error cases
- **Combine techniques:** Error guessing + equivalence partitioning + BVA
- **Document findings:** Every exploratory session should produce test cases or bug reports
- **Maintain checklists:** Update checklist as you find new edge cases
- **Learn from prod incidents:** Add regression tests for each bug found in production
- **Test the tests:** Verify that your test suite can catch bugs (seed bugs intentionally)

---

## Common Bugs Found by Experience-Based Testing

1. **Null handling:** Missing null checks, NullPointerException
2. **Special characters:** SQL injection, XSS, JSON escaping issues
3. **Boundary off-by-one:** Array index out of bounds, fence-post error
4. **Race conditions:** Concurrent modification, non-atomic operations
5. **State inconsistency:** Data mismatch between API response and database
6. **Floating point:** Rounding errors, precision loss
7. **String handling:** Case sensitivity, whitespace, encoding
8. **Timezone/datetime:** Off-by-one hour, daylight saving bugs
9. **Error propagation:** Unhandled exceptions, confusing error messages
10. **Performance:** Timeouts, memory leaks under load

---

## Sample Error Guessing Checklist

Use this for any API endpoint:

```
API: POST /api/offers

Request Body Fuzzing:
□ Missing all fields → 400
□ Empty request body {} → 400
□ Null request body → 400
□ Request body not JSON → 400
□ Extra unknown fields in body → 201? (ignored or error?)
□ Duplicate field names → 400 or last-wins?

Field-by-field:
□ title = null → 400
□ title = "" → 400
□ title = " " → 400 (or trim?)
□ title = "a" * 501 → 400
□ title = "🏨" → 201 (emoji OK)
□ title = "<script>" → 201 (literal, not XSS)
□ price = null → 400
□ price = -1 → 400
□ price = 0 → 201? (free offer)
□ price = "hundred" → 400 (not a number)
□ status = "UNKNOWN" → 400

Headers:
□ Content-Type: application/json missing → 400 or 415?
□ Authorization header missing → 401
□ Authorization header malformed → 401
□ Accept header = "text/html" → 406?

Query Params:
□ Extra unknown params → ignored?
□ Param value with special chars → encoded?

Concurrency:
□ Create same offer twice simultaneously → first wins? 409?
□ Read while creating → see partial data?

Edge Cases:
□ Create at exactly midnight → timestamp correct?
□ Create while DB connection flaky → retry or 500?
□ Create while feature flagged off → 501?
□ Create by user at rate limit → 429?
```
