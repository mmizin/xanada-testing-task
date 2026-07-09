# Using Swagger/OpenAPI Specs for Test Design

Swagger/OpenAPI specs are a goldmine for API test design. They define the contract between API and consumers, making them an excellent source of truth for test cases.

---

## Providing a Swagger URL

**Usage in skill:**
```
/skill-write-api-test-cases <swagger-url> POST /api/offers
```

The skill will fetch the spec and use it to inform test design.

---

## What the Swagger Spec Provides

### 1. Endpoint Signatures

**From OpenAPI:**
```json
{
  "paths": {
    "/api/offers": {
      "post": {
        "summary": "Create a new offer",
        "operationId": "createOffer",
        "tags": ["offers"],
        "requestBody": { ... },
        "responses": { ... }
      }
    }
  }
}
```

**For test design:**
- ✅ HTTP method (POST)
- ✅ Path (/api/offers)
- ✅ Summary / description (context for scenarios)
- ✅ Tags (feature area: offers)

### 2. Request Schema

**From OpenAPI:**
```json
{
  "requestBody": {
    "required": true,
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "required": ["title", "price"],
          "properties": {
            "title": {
              "type": "string",
              "minLength": 1,
              "maxLength": 500,
              "description": "Offer title"
            },
            "price": {
              "type": "number",
              "minimum": 0,
              "maximum": 999999,
              "description": "Price in USD"
            },
            "status": {
              "type": "string",
              "enum": ["ACTIVE", "INACTIVE", "PENDING", "EXPIRED"],
              "description": "Offer status"
            }
          }
        }
      }
    }
  }
}
```

**For test design:**
- ✅ Required fields: title, price → test missing field validation
- ✅ Field types: string, number → test type validation
- ✅ String constraints: minLength=1, maxLength=500 → test boundary cases
- ✅ Number constraints: minimum=0, maximum=999999 → test boundary cases
- ✅ Enum values: ACTIVE, INACTIVE, PENDING, EXPIRED → test invalid enum
- ✅ Descriptions: understand business meaning

**Test cases generated automatically:**
- TC: Missing title → 400
- TC: title empty string → 400
- TC: title at max length (500) → 201
- TC: title exceeds max (501) → 400
- TC: price = -1 (below minimum) → 400
- TC: price = 0 (at minimum) → 201
- TC: price = 999999 (at maximum) → 201
- TC: price = 1000000 (exceeds maximum) → 400
- TC: status = "UNKNOWN" → 400

### 3. Response Schema

**From OpenAPI:**
```json
{
  "responses": {
    "201": {
      "description": "Offer created successfully",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "required": ["id", "title", "price", "created_at"],
            "properties": {
              "id": {
                "type": "string",
                "format": "uuid",
                "description": "Offer ID"
              },
              "title": { "type": "string" },
              "price": { "type": "number" },
              "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO8601 timestamp"
              }
            }
          }
        }
      }
    },
    "400": {
      "description": "Validation error",
      "content": {
        "application/json": {
          "schema": {
            "type": "object",
            "properties": {
              "error": { "type": "string" },
              "message": { "type": "string" },
              "field": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

**For test design:**
- ✅ Success status code: 201
- ✅ Response fields: id, title, price, created_at
- ✅ Field types: UUID format, date-time format
- ✅ Error status code: 400
- ✅ Error response structure: error, message, field
- ✅ Assertions: response contains all required fields, id is UUID, created_at is ISO8601

**Test case assertions generated automatically:**
- Status is 201
- Response id is valid UUID
- Response created_at is ISO8601 format
- Response title matches request
- Response price matches request

### 4. Authentication & Security

**From OpenAPI:**
```json
{
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token"
      }
    }
  },
  "paths": {
    "/api/offers": {
      "post": {
        "security": [{ "bearerAuth": [] }]
      }
    }
  }
}
```

**For test design:**
- ✅ Auth type: Bearer JWT
- ✅ Auth required: yes
- ✅ Scopes: (if defined, e.g., "offer:create")

**Test cases generated automatically:**
- TC: No auth header → 401
- TC: Invalid token → 401
- TC: Expired token → 401
- TC: Token without required scope → 403

### 5. Status Codes

**From OpenAPI:**
```json
{
  "responses": {
    "201": { ... },
    "400": { ... },
    "401": { ... },
    "403": { ... },
    "409": { ... },
    "422": { ... },
    "500": { ... }
  }
}
```

**For test design:**
- ✅ All possible status codes documented
- ✅ Each status code gets a test case
- ✅ Error responses are documented

**Test cases generated automatically:**
- One test per documented status code
- Verify correct error response structure
- Verify correct error message

---

## Test Design Workflow with Swagger

### Step 1: Fetch & Parse
```
Input: RELEASE POST /api/offers
→ Fetch <swagger-url>
→ Parse OpenAPI spec
→ Extract offers.post definition
```

### Step 2: Extract Test Parameters
```
From spec:
  - Method: POST
  - Path: /api/offers
  - Required fields: title, price
  - Field constraints: title 1-500 chars, price 0-999999
  - Status codes: 201, 400, 401, 403, 409, 422
  - Auth: Bearer JWT
```

### Step 3: Generate Test Cases
```
Equivalence Partitioning:
  title: [empty, valid, too-long] → test 3 cases
  price: [negative, zero, normal, too-high] → test 4 cases
  auth: [missing, invalid, valid] → test 3 cases
  
Boundary Value Analysis:
  title length: 0, 1, 500, 501 → test 4 cases
  price: -1, 0, 1, 999998, 999999, 1000000 → test 6 cases

Decision Table:
  auth × valid_body → 4 combinations

Total: ~15–20 test cases from spec alone
```

### Step 4: Supplement with Exploratory Testing
```
Spec doesn't cover:
  - Concurrent requests (race conditions)
  - Rate limiting (documented separately?)
  - Edge cases (unicode, special chars, null values)
  - Business rules beyond validation (e.g., "can't update deleted offer")

→ Add ~5–10 exploratory tests
```

---

## Common Gaps in Swagger Specs

Not everything is documented in Swagger. Watch for:

### 1. Business Rules Not in Schema
```
Spec says: price is a number, 0–999999
Spec doesn't say: 
  - "Free offers (price=0) only allowed for first-time users"
  - "Price must match currency (USD/EUR different ranges)"
  
→ Add tests for business rules beyond schema validation
```

### 2. Error Cases Not Listed
```
Spec documents: 201, 400, 401, 403
Spec doesn't list: 409 (conflict, offer already exists)
                   422 (unprocessable, derived field mismatch)
                   503 (dependency unavailable)
→ Add tests for likely error cases
```

### 3. State Transitions Not Documented
```
Spec for PUT /api/offers/{id}:
  - Field: status (enum: ACTIVE, INACTIVE, PENDING, EXPIRED)
  
Spec doesn't say:
  - "Can only transition from DRAFT to ACTIVE, not EXPIRED to ACTIVE"
  - "Can delete (set status=DELETED) from any state"
  
→ Add state transition tests
```

### 4. Concurrency Not Addressed
```
Spec doesn't mention:
  - What happens if two users update same offer simultaneously
  - Is there optimistic locking (version field)?
  - Does last-write-win, or return 409 conflict?
  
→ Add concurrency tests
```

### 5. Sensitive Data Not Called Out
```
Spec documents all response fields
Spec doesn't flag:
  - "Do not return user passwords in responses"
  - "Do not return payment tokens"
  
→ Add security tests to verify sensitive data not leaked
```

---

## Using Swagger for Coverage Analysis

### Generate Coverage Report from Spec

```bash
# Count endpoints in spec
curl -s <swagger-url> | jq '.paths | keys | length'
→ 35 endpoints total

# Count test cases
grep "^## TC-" test-cases/api/*.md | wc -l
→ 28 test cases

# Coverage
28 / 35 = 80% endpoints covered
→ Which 7 endpoints lack tests? (Add them)
```

### Coverage Matrix

| Endpoint | Method | Tests | Status |
|---|---|---|---|
| /api/offers | POST | 8 | ✅ Complete |
| /api/offers | GET | 6 | ✅ Complete |
| /api/offers/{id} | GET | 5 | ✅ Complete |
| /api/offers/{id} | PUT | 7 | ✅ Complete |
| /api/offers/{id} | DELETE | 4 | ✅ Complete |
| /api/offers/search | GET | 10 | ✅ Complete |
| /api/users | POST | 8 | ✅ Complete |
| /api/users/{id} | GET | 3 | ⚠️ Minimal |
| /api/bookings | POST | 0 | ❌ Missing |

**Action:** Add tests for endpoints with minimal or missing coverage.

---

## Tips for Using Swagger

### ✅ Do:
- **Use spec as source of truth** — If spec says minLength=1, test it
- **Extract test parameters** — constraints, field types, enums → test cases
- **Supplement with exploratory tests** — Spec doesn't cover everything
- **Update tests when spec changes** — Keep them in sync
- **Document deviations** — If implementation differs from spec, flag it

### ❌ Don't:
- **Rely solely on spec** — Spec can be incomplete or out-of-date
- **Hardcode spec values** — Use assertions to verify, not hardcoded checks
- **Forget business rules** — Spec shows schema, not business logic
- **Skip error testing** — Spec may not list all error cases
- **Ignore concurrency** — Spec rarely covers concurrent scenarios

---

## Automation Decision for Spec-Based Tests

For tests generated directly from Swagger spec:

```
Most spec-based tests → AUTOMATE_API ✅
  ✓ Contract is stable (published in spec)
  ✓ Low flakiness (deterministic input validation)
  ✓ Business-critical (test the API contract)

Exception: tests for undocumented error cases → DEFER_INTEGRATION
  ✓ Less stable (may change as spec evolves)
  ✓ May be flaky (depends on system state)
  ✓ Defer until error contract stabilizes
```

---

## Tools for Working with Swagger

```bash
# Validate spec
npm install -g @apidevtools/swagger-cli
swagger-cli validate <swagger-url>

# Convert to JSON (if YAML)
npm install -g swagger-to-postman
swagger-to-postman -s spec.yaml -o spec.json

# Generate code from spec
npm install -g openapi-generator-cli
openapi-generator-cli generate -i spec.json -g python -o generated/

# Mock server from spec
npm install -g prism-cli
prism mock spec.json
```

---

## Example: Design Tests from Swagger for POST /api/offers

```
1. Fetch spec: <swagger-url>

2. Extract endpoint definition:
   - Method: POST
   - Path: /api/offers
   - Required fields: title, price, status
   - Field constraints:
     * title: string, 1-500 chars
     * price: number, 0-999999
     * status: enum (ACTIVE, INACTIVE, PENDING, EXPIRED)
   - Auth: Bearer JWT
   - Status codes: 201, 400, 401, 403, 409

3. Generate test cases:
   [TC-001] Create offer with valid data → 201
   [TC-002] Create offer without title → 400
   [TC-003] Create offer with title = "" → 400
   [TC-004] Create offer with title.length = 500 → 201
   [TC-005] Create offer with title.length = 501 → 400
   [TC-006] Create offer with price = -1 → 400
   [TC-007] Create offer with price = 0 → 201
   [TC-008] Create offer with price = 999999 → 201
   [TC-009] Create offer with price = 1000000 → 400
   [TC-010] Create offer without auth → 401
   [TC-011] Create offer with invalid token → 401
   [TC-012] Create offer with invalid status → 400
   [TC-013] Create duplicate offer (offer already exists) → 409

4. Supplement with exploratory tests:
   [TC-014] Create offer with unicode in title → 201
   [TC-015] Create offer with special chars (injection) → 201
   [TC-016] Create offer concurrently (race condition) → first wins/409?
   [TC-017] Verify response id is UUID format → 201 with valid UUID
   [TC-018] Verify response created_at is ISO8601 → 201 with timestamp

Total: 18 test cases from spec + exploration
```

---

## Summary

**Swagger is invaluable for test design because it:**
- Provides exact field constraints, types, and ranges
- Documents all status codes and responses
- Specifies required fields and authentication
- Serves as source of truth for API contract
- Enables automated test generation

**But always supplement with:**
- Business rule testing (beyond schema)
- Error case exploration (gaps in spec)
- Concurrency/state testing (not in spec)
- Security testing (sensitive data handling)
- User scenario testing (use cases)

**Use the spec to start, exploratory testing to finish.**
