# Black-Box Testing Techniques for APIs

Black-box testing validates the **input/output behavior** of an API endpoint without knowledge of internal code. Focus on: valid/invalid inputs, boundary conditions, state transitions, and error responses.

---

## 1. Equivalence Partitioning

**Idea:** Group inputs into classes that should behave identically. Test one value from each class.

**How to use:**
- Partition input into valid and invalid classes
- Partition by data type (string, number, enum)
- Partition by business meaning (e.g., "offer status": ACTIVE, INACTIVE, PENDING, EXPIRED)

**Example: Create Offer Endpoint**

```
Request field: title
Classes:
  ✅ Valid:   Non-empty string, 1–500 characters
  ❌ Invalid: Empty string, > 500 characters, null, non-string (number, boolean)

Request field: price
Classes:
  ✅ Valid:   Positive number (0.01–999999)
  ❌ Invalid: Negative, zero, > 999999, non-number, string

Request field: status (enum)
Classes:
  ✅ Valid:   "ACTIVE", "INACTIVE", "PENDING", "EXPIRED"
  ❌ Invalid: "active" (lowercase), "UNKNOWN", null, number
```

**Test Cases:**
- TC-001: title (valid class) → expect 201
- TC-002: title = "" (invalid/empty) → expect 400
- TC-003: title with 500 chars (boundary) → expect 201
- TC-004: price = 100 (valid) → expect 201
- TC-005: price = -1 (invalid/negative) → expect 400
- TC-006: status = "ACTIVE" (valid) → expect 201
- TC-007: status = "UNKNOWN" (invalid) → expect 400

**When to use:** Every endpoint with structured input (query params, request body).

---

## 2. Boundary Value Analysis (BVA)

**Idea:** Test at the **edges** of valid input ranges.

**Boundaries to test:** min−1, min, min+1, max−1, max, max+1

**Example: Search Offers with Price Range**

```
Field: min_price (min = 0, max = 999999)
Boundaries:
  -1        (below minimum)
  0         (at minimum)
  1         (above minimum)
  999998    (below maximum)
  999999    (at maximum)
  1000000   (above maximum)

Field: page_size (min = 1, max = 100)
Boundaries:
  0         (below minimum)
  1         (at minimum)
  2         (above minimum)
  99        (below maximum)
  100       (at maximum)
  101       (above maximum)
```

**Test Cases:**
- TC-010: min_price = -1 → expect 400 (below minimum)
- TC-011: min_price = 0 → expect 200 (at minimum)
- TC-012: min_price = 1 → expect 200 (above minimum)
- TC-020: page_size = 0 → expect 400 (below minimum)
- TC-021: page_size = 1 → expect 200 (at minimum)
- TC-022: page_size = 100 → expect 200 (at maximum)
- TC-023: page_size = 101 → expect 400 (above maximum)

**When to use:** Any numeric, string length, or array-size input.

---

## 3. Decision Table Testing

**Idea:** Test **combinations** of input conditions and their effects on output.

**How to use:**
1. List all input conditions (binary: true/false, or multi-value)
2. List expected outputs/effects
3. Create a table with all meaningful combinations
4. Generate test cases from each row

**Example: Create Offer with Auth & Permission Check**

```
Conditions:
  A = User authenticated (true/false)
  B = User has 'offer:create' permission (true/false)
  C = Request body valid (true/false)

Truth Table:
| A | B | C | Expected Status | Effect |
|---|---|---|---|---|
| F | F | F | 401 | Reject: no auth |
| F | T | F | 401 | Reject: no auth (permission irrelevant) |
| T | F | F | 403 | Reject: auth OK, permission denied |
| T | T | F | 400 | Reject: auth OK, permission OK, invalid body |
| T | T | T | 201 | Success: create offer |
```

**Test Cases:**
- TC-030: No auth, invalid body → 401
- TC-031: No auth, valid body → 401
- TC-032: Auth, no permission, invalid body → 403
- TC-033: Auth, no permission, valid body → 403
- TC-034: Auth, permission, invalid body → 400
- TC-035: Auth, permission, valid body → 201 ✅

**When to use:** Endpoints with multiple conditions (auth, roles, flags, feature gates).

---

## 4. State Transition Testing

**Idea:** Test **valid and invalid state changes** for resources with lifecycle (DRAFT → ACTIVE → INACTIVE, etc.).

**How to use:**
1. Define all possible states
2. Map valid transitions (ACTIVE → INACTIVE OK, INACTIVE → DELETED OK, etc.)
3. Map invalid transitions (DELETED → ACTIVE not allowed)
4. Test each path

**Example: Offer Lifecycle**

```
States: DRAFT, ACTIVE, INACTIVE, EXPIRED, DELETED

Valid Transitions:
  DRAFT → ACTIVE ✅
  ACTIVE → INACTIVE ✅
  INACTIVE → ACTIVE ✅
  ACTIVE → EXPIRED ✅ (system transition)
  any → DELETED ✅ (soft delete)

Invalid Transitions:
  DRAFT → DELETED ✗ (must be active/inactive first)
  EXPIRED → ACTIVE ✗ (expired offers can't be reactivated)
  DELETED → any ✗ (deleted offers are final)
```

**Test Cases:**
- TC-040: Update offer from DRAFT to ACTIVE → 200 ✅
- TC-041: Update offer from ACTIVE to INACTIVE → 200 ✅
- TC-042: Update offer from INACTIVE to ACTIVE → 200 ✅
- TC-043: Update offer from DRAFT to DELETED → 400 (invalid transition)
- TC-044: Update offer from EXPIRED to ACTIVE → 400 (invalid transition)
- TC-045: Update deleted offer → 404 or 410 (already deleted)

**When to use:** Resources with state/lifecycle (orders, offers, users, bookings).

---

## 5. Domain Analysis Testing

**Idea:** Test **correlated parameters together** (not independently). Some parameter combinations are only valid if used together.

**Example: Search Offers with Date Range**

```
Domain: Travel dates
  check_in: date
  check_out: date
  nights: number (derived)

Valid combinations:
  check_in < check_out → nights = check_out - check_in ✅
  check_in = check_out → nights = 0 or 1 (depends on business rule) ?
  check_in > check_out → invalid ✗

Domain: Location search
  location: string (city name)
  radius: number (miles)
  latitude/longitude: coordinates

Valid combinations:
  location alone → use city's center coordinates ✅
  latitude/longitude alone → use exact coordinates ✅
  location + radius → search within radius of city ✅
  location + latitude/longitude → contradiction ✗ (invalid)
```

**Test Cases:**
- TC-050: check_in = 2025-06-28, check_out = 2025-07-05 → nights = 7 ✓
- TC-051: check_in = 2025-07-05, check_out = 2025-06-28 → 400 (invalid date order)
- TC-052: location = "Paris", radius = 10 → search Paris ± 10 miles ✓
- TC-053: location = "Paris", latitude=48.8, longitude=2.3 → 400 (location or coordinates, not both)

**When to use:** Multi-parameter inputs where values must be logically consistent.

---

## 6. Cause-Effect Graph

**Idea:** Map **causes** (input conditions) to **effects** (output outcomes). Generate combinations that exercise all cause-effect relationships.

**How to use:**
1. List causes (input conditions)
2. List effects (observable outcomes)
3. Draw graph mapping causes to effects
4. Use graph to generate minimal test set

**Example: User Registration**

```
Causes:
  C1: Email valid
  C2: Email not in system (unique)
  C3: Password >= 8 chars
  C4: Age >= 18

Effects:
  E1: User created (201)
  E2: Email validation error (400)
  E3: Email already exists (409)
  E4: Password too weak (400)
  E5: Age verification error (400)

Relationships:
  C1 ∧ C2 ∧ C3 ∧ C4 → E1 (all valid → create)
  ¬C1 → E2 (invalid email → validation error)
  C1 ∧ ¬C2 → E3 (email exists → conflict)
  C1 ∧ C2 ∧ ¬C3 → E4 (password weak → error)
  C1 ∧ C2 ∧ C3 ∧ ¬C4 → E5 (age invalid → error)
```

**Test Cases (minimal set covering all effects):**
- TC-060: C1, C2, C3, C4 all true → E1 (success)
- TC-061: ¬C1 (invalid email) → E2
- TC-062: C1, ¬C2 (duplicate email) → E3
- TC-063: C1, C2, ¬C3 (weak password) → E4
- TC-064: C1, C2, C3, ¬C4 (age < 18) → E5

**When to use:** Complex logic with multiple inputs affecting single output.

---

## 7. Use Case Testing

**Idea:** Test the **main flow, alternative flows, and exception flows** of a use case.

**How to use:**
1. Define the main happy-path (user's primary goal)
2. Define alternative flows (valid variations, branching)
3. Define exception flows (errors, user corrections)

**Example: Search & Book Offer**

```
Main Flow (Happy Path):
  1. User enters search criteria (location, dates)
  2. API returns matching offers
  3. User selects offer
  4. User enters payment info
  5. API creates booking
  6. Return confirmation

Alternative Flows:
  Alt-A: User refines search (different dates) → return refined results
  Alt-B: User views offer details before booking → return details + reviews
  Alt-C: User cancels booking before payment → return 200 (no booking created)

Exception Flows:
  Exc-1: Search returns no results → return 200 with empty array
  Exc-2: Invalid search parameters → return 400
  Exc-3: Offer no longer available → return 410 or 409
  Exc-4: Payment fails → return 402 (payment required) or 422 (unprocessable)
```

**Test Cases:**
- TC-070: Main flow (search + book) → 201 booking created
- TC-071: Alt-A: Refine search → 200 refined results
- TC-072: Alt-B: View offer details → 200 details + reviews
- TC-073: Exc-1: No results → 200 empty array
- TC-074: Exc-2: Invalid parameters → 400
- TC-075: Exc-3: Offer unavailable → 410 or 409
- TC-076: Exc-4: Payment fails → 402

**When to use:** Multi-step workflows (booking flow, checkout, registration).

---

## 8. Pairwise Testing

**Idea:** Test **every pair** of parameter values, minimizing the total number of tests.

**How to use:**
- When you have many parameters with few values each
- Generate combinations such that every pair (A, B) appears in at least one test

**Example: Filter Offers**

```
Parameters:
  room_type: [STUDIO, 1BR, 2BR, VILLA] (4 values)
  pet_friendly: [true, false] (2 values)
  wheelchair_accessible: [true, false] (2 values)
  sort_by: [PRICE, RATING, NEWEST] (3 values)

Exhaustive combinations: 4 × 2 × 2 × 3 = 48 tests
Pairwise coverage: 8–10 tests (covers every pair)
```

**Pairwise Test Cases:**
```
| room_type | pet | wheelchair | sort_by | Notes |
|-----------|-----|-----------|---------|-------|
| STUDIO | T | T | PRICE | pair: (STUDIO, PRICE), (pet, sort) |
| 1BR | F | T | RATING | pair: (1BR, RATING), (F, T) |
| 2BR | T | F | NEWEST | pair: (2BR, NEWEST), (T, F) |
| VILLA | F | F | PRICE | pair: (VILLA, PRICE), (F, PRICE) |
| STUDIO | F | T | RATING | pair: (STUDIO, RATING) |
| 1BR | T | F | NEWEST | pair: (1BR, NEWEST) |
| ... | ... | ... | ... | (continue until all pairs covered) |
```

**When to use:** Many independent parameters, combinatorial explosion of possibilities.

---

## Summary Table: When to Use Each Technique

| Technique | When to Use | Example |
|---|---|---|
| **Equivalence Partitioning** | Every input field, group by valid/invalid | title: empty vs. valid vs. too long |
| **Boundary Value Analysis** | Numeric/string-length/array inputs | price: -1, 0, 1, 999998, 999999, 1000000 |
| **Decision Table** | Multiple conditions affecting one outcome | auth + permission + valid_body → result |
| **State Transition** | Resources with lifecycle states | offer: DRAFT → ACTIVE → INACTIVE → DELETED |
| **Domain Analysis** | Correlated multi-parameter inputs | check_in + check_out (must be ordered) |
| **Cause-Effect Graph** | Complex logic, many causes → effects | registration: 4 inputs → 5 possible outcomes |
| **Use Case Testing** | Multi-step workflows | search + select + book (happy path + errors) |
| **Pairwise Testing** | Many parameters, combinatorial explosion | 4 room types × 3 price ranges × 2 pet policies |

---

## Tips

- **Combine techniques:** A good test suite uses multiple techniques on the same endpoint
- **Start with equivalence partitioning:** It's the simplest and most valuable
- **Add BVA for numbers:** Every number needs boundary tests
- **Use decision table for auth/permissions:** Catches security gaps
- **Use state transitions for resources:** Prevents invalid state bugs
- **Focus on boundaries and error cases:** That's where bugs hide
