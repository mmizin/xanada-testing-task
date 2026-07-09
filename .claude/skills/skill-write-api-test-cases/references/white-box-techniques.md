# White-Box Testing Techniques for APIs

White-box testing validates **internal code structure** — branches, loops, and paths. You need to read the code to apply these techniques.

---

## 1. Statement Coverage

**Idea:** Every line of code executes at least once.

**How to use:**
1. Read the function/method source code
2. Identify every executable statement
3. Write tests that cause each statement to execute

**Example: Price Validation Function**

```python
def validate_offer(offer):
    if offer.price < 0:                    # Line 2
        return False, "Price cannot be negative"  # Line 3
    
    if offer.price > 999999:               # Line 5
        return False, "Price exceeds maximum"    # Line 6
    
    if not offer.title:                    # Line 8
        return False, "Title is required"  # Line 9
    
    return True, "Valid"                   # Line 11
```

**Statement Coverage (Needs 4 tests):**
- TC-001: price = 100, title = "Apt" → executes lines 2, 5, 8, 11 ✅ (all happy path)
- TC-002: price = -1, title = "Apt" → executes line 3 (price < 0 check)
- TC-003: price = 1000000, title = "Apt" → executes line 6 (price > max check)
- TC-004: price = 100, title = "" → executes line 9 (title check)

**When to use:** Quick coverage baseline. "Are all lines executed?"

---

## 2. Decision / Branch Coverage

**Idea:** Every true/false branch executes at least once.

**How to use:**
1. Identify each if/else, while, for branch
2. Write tests to execute both true AND false for each condition

**Example: Check If Offer Is Available**

```python
def is_available(offer):
    if offer.status == "ACTIVE":           # Branch A
        if offer.quantity > 0:             # Branch B
            return True                    # True path for both A and B
        else:
            return False                   # False path for B (A is true)
    else:
        return False                       # False path for A
```

**Branch Coverage (Needs 3 tests):**
- TC-001: status = "ACTIVE", quantity = 5 → A=T, B=T → return True
- TC-002: status = "ACTIVE", quantity = 0 → A=T, B=F → return False
- TC-003: status = "INACTIVE", quantity = 5 → A=F → return False

**Coverage matrix:**
```
| Test | A | B | Result |
|------|---|---|--------|
| TC-001 | T | T | True |
| TC-002 | T | F | False |
| TC-003 | F | - | False |
```

**When to use:** More thorough than statement coverage. Catches missing else branches.

---

## 3. Condition Testing

**Idea:** Every atomic condition evaluates to true AND false.

**How to use:**
1. Break compound conditions into atomic parts
2. Test each part both true and false

**Example: Complex Condition**

```python
def can_book(user, offer):
    if (user.age >= 18) and (offer.available) and (user.payment_valid):
        return True
    return False
```

**Atomic conditions:**
- C1 = user.age >= 18
- C2 = offer.available
- C3 = user.payment_valid

**Condition Testing (Needs 6 tests, one per condition):**
- TC-001: C1=T, C2=T, C3=T → True
- TC-002: C1=F, C2=T, C3=T → False (C1 false)
- TC-003: C1=T, C2=F, C3=T → False (C2 false)
- TC-004: C1=T, C2=T, C3=F → False (C3 false)
- (Plus variations to isolate each condition)

**When to use:** When conditions have multiple atomic parts.

---

## 4. Path Testing

**Idea:** Every linearly independent path through the code executes at least once.

**How to use:**
1. Draw a control flow graph (nodes = statements, edges = branches)
2. Calculate cyclomatic complexity: V(G) = branches + 1
3. Write V(G) tests to cover all paths

**Example: Search with Filtering**

```python
def search_offers(filters):
    results = []
    
    if filters.location:                   # Branch A
        results = search_by_location(filters.location)
    else:
        results = all_offers()
    
    if filters.price_max:                  # Branch B
        results = [r for r in results if r.price <= filters.price_max]
    
    if filters.pet_friendly:               # Branch C
        results = [r for r in results if r.pet_friendly]
    
    return results
```

**Paths (A × B × C = 2 × 2 × 2 = 8 paths):**
```
| Path | A | B | C | Filters |
|------|---|---|---|---------|
| 1 | T | T | T | location + price_max + pet |
| 2 | T | T | F | location + price_max |
| 3 | T | F | T | location + pet |
| 4 | T | F | F | location |
| 5 | F | T | T | price_max + pet |
| 6 | F | T | F | price_max |
| 7 | F | F | T | pet |
| 8 | F | F | F | no filters |
```

**Test Cases (8 tests for 8 paths):**
- TC-001: All filters → results filtered by all three
- TC-002: Location + price → results filtered by location and price
- TC-003: Location + pet → results filtered by location and pet
- ... (continue for all 8 combinations)

**When to use:** Complex branching with nested conditions.

---

## 5. Loop Coverage

**Idea:** Test loops for 0, 1, and typical/max iterations.

**How to use:**
- Zero iterations: bypass loop entirely
- One iteration: execute loop body once
- Typical iterations: multiple iterations (2, 3, n)
- Max iterations: test upper boundary
- Max+1 iterations: test overflow condition

**Example: Batch Update Offers**

```python
def update_offers_batch(offer_ids):
    updated = []
    for offer_id in offer_ids:             # Loop
        offer = db.get(offer_id)
        offer.status = "ACTIVE"
        db.save(offer)
        updated.append(offer)
    return updated
```

**Loop Coverage:**
- TC-001: offer_ids = [] → 0 iterations, returns empty array
- TC-002: offer_ids = [id1] → 1 iteration, returns 1 offer
- TC-003: offer_ids = [id1, id2, id3] → 3 iterations, returns 3 offers
- TC-004: offer_ids = [id1, ... id100] → max iterations (100)
- TC-005: offer_ids = [id1, ... id101] → max+1 (overflow), returns error or clips

**When to use:** Any loop or iteration (for, while, list comprehension).

---

## 6. Exception Coverage

**Idea:** Test that all exception paths are triggered and handled correctly.

**How to use:**
1. Identify all try/except blocks
2. Identify all places exceptions can occur
3. Write tests that trigger each exception
4. Verify correct error handling (log, response, state rollback)

**Example: Database Transaction**

```python
def create_offer(offer_data):
    try:
        db.begin()
        offer = Offer(**offer_data)
        db.add(offer)
        db.commit()                        # May raise DatabaseError
        return offer
    except DatabaseError as e:
        db.rollback()                      # Cleanup
        return None, f"DB Error: {e}"
    except ValueError as e:
        return None, f"Validation Error: {e}"
```

**Exception Coverage:**
- TC-001: Valid data → commit succeeds, offer returned
- TC-002: DB connection fails → DatabaseError, rollback called, error returned
- TC-003: Invalid data (ValueError) → rollback called, error returned
- TC-004: DB connection recovered after rollback → next request succeeds (state clean)

**Assertions for exception tests:**
- Database state rolled back (no orphaned offer)
- Error message returned to client
- Logging captured exception details
- System recovers for next request

**When to use:** Any error handling (try/except, validation, external API calls).

---

## 7. Multiple Condition Coverage (MCC)

**Idea:** Test all 2^N combinations of atomic conditions.

**How to use:**
1. Break compound condition into atomic conditions
2. Generate all 2^N combinations
3. Write test for each combination

**Example: Can User Update Offer?**

```python
def can_update_offer(user, offer):
    if (user.is_owner and offer.is_draft) or (user.is_admin and offer.exists):
        return True
    return False
```

**Atomic conditions:**
- C1 = user.is_owner
- C2 = offer.is_draft
- C3 = user.is_admin
- C4 = offer.exists

**All 2^4 = 16 combinations:**
```
| C1 | C2 | C3 | C4 | Result |
|----|----|----|----|----|
| T | T | T | T | T (first part true) |
| T | T | T | F | T (first part true) |
| T | T | F | T | T (first part true) |
| T | T | F | F | T (first part true) |
| T | F | T | T | T (second part true) |
| T | F | T | F | F |
| T | F | F | T | F |
| T | F | F | F | F |
| F | T | T | T | T (second part true) |
| F | T | T | F | F |
| F | T | F | T | F |
| F | T | F | F | F |
| F | F | T | T | T (second part true) |
| F | F | T | F | F |
| F | F | F | T | F |
| F | F | F | F | F |
```

**Test Cases (16 tests for all combinations):**
- TC-001: owner, draft, admin, exists → True (owner + draft)
- TC-002: owner, draft, admin, not_exists → True (owner + draft)
- ... (one per combination)

**When to use:** Critical business logic with complex conditions (access control, payment rules).

---

## 8. MC/DC Coverage (Modified Condition/Decision Coverage)

**Idea:** Each condition must **independently affect** the outcome (stronger than MCC).

**How to use:**
1. Identify atomic conditions
2. For each condition, find test pairs where:
   - The condition changes from T → F
   - The outcome changes due to that condition
   - All other conditions held constant

**Example: Booking Allowed?**

```python
def allow_booking(user_age_ok and payment_valid and offer_available):
    return result
```

**MC/DC Test Pairs (3 pairs for 3 conditions):**

For C1 (age):
- Test where C1=T, outcome=T
- Test where C1=F, outcome=F (keeping C2, C3 constant)

For C2 (payment):
- Test where C2=T, outcome=T
- Test where C2=F, outcome=F

For C3 (availability):
- Test where C3=T, outcome=T
- Test where C3=F, outcome=F

**When to use:** Safety-critical code, financial transactions, access control.

---

## Summary Table: White-Box Coverage Types

| Coverage Type | Complexity | When to Use | Example Count |
|---|---|---|---|
| **Statement** | Low | Quick baseline | ~10% of black-box tests |
| **Decision/Branch** | Low-Med | Most code | ~20% of black-box tests |
| **Condition** | Medium | Multi-part conditions | Extra tests for complex logic |
| **Path** | Medium-High | Nested branches | 2^N tests for N branches |
| **Loop** | Low | Any iteration | 4–5 tests per loop |
| **Exception** | Medium | Error handling | ~5–10% of tests |
| **MCC** | High | Complex logic | 2^N tests (explosive growth) |
| **MC/DC** | Very High | Safety-critical | ~2N tests (manageable) |

---

## Tips

- **Start with statement + decision:** Gets to 80% coverage with minimal effort
- **Add loop coverage:** Test 0, 1, typical, max iterations
- **Add exception coverage:** Every try/except and error path
- **Use MCC/MC/DC for critical code:** Payment, auth, booking logic
- **Don't aim for 100% coverage:** Focus on value; some paths aren't worth testing
- **Combine with black-box:** Black-box tests find bugs; white-box tests find gaps in code paths

---

## Tools for White-Box Testing (Python)

```bash
# Install coverage tool
pip install coverage pytest-cov

# Run tests with coverage
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# View coverage by file
coverage report -m
```

**Coverage report output:**
```
Name                          Stmts   Miss  Cover
-----------------------------------------------
src/api/offers.py                42     8    81%
src/api/search.py                28     2    93%
src/infrastructure/db.py          15     3    80%
-----------------------------------------------
TOTAL                            85    13    85%
```

- **Stmts:** Total statements
- **Miss:** Statements not executed
- **Cover:** Percentage of coverage
