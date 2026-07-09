# API Test Case Template

## Header

```
# <Feature Name> — API Test Cases

**Endpoint:** `<HTTP_METHOD> <path>` (e.g., `POST /api/offers`)
**Techniques Applied:** Equivalence Partitioning, Boundary Value Analysis, State Transition Testing
**Coverage Type:** Happy-path, Error Cases, Boundary Cases
**Generated:** YYYY-MM-DD
```

---

## Test Case Format

Each test case follows this structure:

```
## TC-001: <Scenario Name>

**Tags:** @smoke @regression @feature @type

**Technique:** [Equivalence Partitioning | Boundary Value Analysis | Decision Table | State Transition | etc.]

**Pre-conditions:**
- [State/data that must exist before test runs]
- [Example: "An offer with status=ACTIVE exists in database"]

**Request:**
- **Method:** POST
- **Path:** `/api/offers`
- **Headers:** Content-Type: application/json, Authorization: Bearer <valid_token>
- **Query Params:** (if applicable)
  - `page=1`
  - `limit=10`
- **Body:**
  ```json
  {
    "title": "Beach Apartment",
    "price": 150,
    "bedrooms": 2
  }
  ```

**Expected Response:**
- **Status Code:** 201
- **Headers:** Content-Type: application/json
- **Body Schema:**
  ```json
  {
    "id": "<string: UUID>",
    "title": "<string>",
    "price": "<number: >= 0>",
    "created_at": "<ISO8601 timestamp>"
  }
  ```
- **Assertions:**
  - Response status is 201
  - Response body contains all required fields
  - Response `id` is a valid UUID
  - Response `created_at` is current timestamp (within 1 second)

**Test Data:**
- Valid JWT token with appropriate scopes
- Valid offer payload with required fields
- Price value in valid range (0–999999)

**Test Data Setup:**
For data-dependent cases, describe the characteristic needed instead of hardcoding values:
- "Valid JWT token from authenticated user with 'offer:create' scope" → resolved at test runtime from fixture
- "A room availability record from the current date forward" → resolved from fixture that queries database
- "An existing offer with at least 5 reviews" → resolved by fixture that creates/finds matching record

---

## TC-002: Create Offer with Missing Required Field

**Tags:** @regression @negative @validation @offers

**Technique:** Equivalence Partitioning (invalid input class)

**Pre-conditions:**
- User is authenticated with valid token
- User has 'offer:create' permission

**Request:**
- **Method:** POST
- **Path:** `/api/offers`
- **Headers:** Content-Type: application/json, Authorization: Bearer <valid_token>
- **Body:**
  ```json
  {
    "price": 150
    // Missing "title" field
  }
  ```

**Expected Response:**
- **Status Code:** 400
- **Body Schema:**
  ```json
  {
    "error": "validation_error",
    "message": "Missing required field: title",
    "field": "title"
  }
  ```
- **Assertions:**
  - Response status is 400
  - Error message identifies missing field
  - No offer created in database

**Test Data:**
- Valid price value
- Missing required field intentionally

---

## TC-003: Search Offers with Boundary Price Range

**Tags:** @regression @boundary @search @offers

**Technique:** Boundary Value Analysis

**Pre-conditions:**
- At least 5 offers exist in database with varying prices
- Offers with prices: 50, 100, 150, 200, 250

**Request:**
- **Method:** GET
- **Path:** `/api/offers/search`
- **Query Params:**
  - `min_price=100`
  - `max_price=200`

**Expected Response:**
- **Status Code:** 200
- **Body:**
  ```json
  {
    "results": [
      { "id": "...", "title": "...", "price": 100 },
      { "id": "...", "title": "...", "price": 150 },
      { "id": "...", "title": "...", "price": 200 }
    ],
    "total": 3
  }
  ```
- **Assertions:**
  - Status 200
  - All results have price >= 100 AND price <= 200
  - Offers with prices 50 and 250 not included
  - Total count matches results length

**Test Data:**
- min_price and max_price as boundary values
- Multiple offers in database across price ranges

---

## Tips for Writing Good Test Cases

### ✅ Do:
- **Name clearly:** "Create offer with valid data returns 201" (not "test_create_offer")
- **Explicit pre-conditions:** Don't assume database state; state it clearly
- **Concrete stable data:** Use real values for HTTP methods, status codes, field types
- **Describe characteristics for unstable data:** "a valid offer ID" not "offer_id: 1026051"
- **Separate test data setup:** Use fixtures to resolve characteristics at runtime
- **Specific assertions:** "Response status is 201" not "Response is successful"
- **Observable outcomes:** "Returns 401 with error 'unauthorized'" not "Fails"

### ❌ Don't:
- **Hardcode entity IDs:** "offer_id: 1026051" → "a valid offer ID from fixture"
- **Hardcode timestamps:** "created_at: 2025-06-27T10:30:00Z" → "current timestamp (within 1 second)"
- **Vague expectations:** "response should be correct" → "status 200, schema matches spec, price >= 0"
- **Repeat pre-condition setup:** If pre-condition says "authenticated user", don't repeat auth in steps
- **Test multiple scenarios in one case:** One scenario per test case (one assertion focus)
- **Assume implicit state:** State all assumptions in pre-conditions

### 🔄 Test Data Setup Pattern

When a test needs specific data characteristics:

**Instead of hardcoding:**
```
"offer_id": "9da3e3f2-c7b6-4e8b-a5d9-3b8c5f2a1e9d"
```

**Use a characteristic description:**
```
**Test Data Setup:**
- "A valid offer ID" → resolved at runtime by fixture that queries for any valid offer
- "An offer with zero reviews" → resolved by fixture that finds/creates matching offer
```

At test implementation time, the fixture knows how to resolve these characteristics from the database or create them dynamically.
