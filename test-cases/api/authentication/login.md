# Authentication (Login) — API Test Cases

**Endpoint:** `POST /bpapi/rest/security/session` (Matchbook API)
**Techniques Applied:** Equivalence Partitioning, Boundary Value Analysis, Decision Table, Error Guessing, Use Case Testing, Checklist-Based
**Coverage Type:** Happy-path, Error Cases, Boundary Cases, Security Cases
**Generated:** 2026-07-08
**Traceability:** PRD-001 (FR-x.y references) via TD-001 §4 coverage matrix

> **Isolation category** (per Architecture Design §4 / TD-001 §3) is stated on
> every case: `stateless` (parallel-safe), `session-state` (controlled isolation),
> `account-state` (atomic, non-interleaving). Negative-credential cases use
> synthetic non-existent usernames per the TD-001 §5 test data strategy — only
> TC-006 touches the real account's failure counter, and it recovers within the
> same case.

> **Note on expected status codes:** the public docs document `400` for failures.
> Where the real API might reasonably differ (e.g. `401` for bad credentials,
> `405` for wrong method, `415` for wrong content type), the assertion is "the
> documented code or another 4xx — never 5xx", to be tightened after the first
> exploratory run (PRD-001 §10 risk).

---

## TC-001: Login with valid credentials returns 200 and a session token

**Tags:** @smoke @critical @contract @auth
**Technique:** Equivalence Partitioning (valid class) — FR-1.1
**Isolation:** session-state

**Pre-conditions:**
- Valid test account credentials available from configuration (never hardcoded).
- Account is not suspended.

**Request:**
- **Method:** POST
- **Path:** `/bpapi/rest/security/session`
- **Headers:** Content-Type: application/json
- **Body:**
  ```json
  { "username": "<valid username>", "password": "<valid password>" }
  ```

**Expected Response:**
- **Status Code:** 200
- **Assertions:**
  - Response status is 200.
  - Response contains a non-empty `session-token` (body and/or cookie/header).
  - Response does not echo the password anywhere.

**Test Data Setup:**
- "Valid credentials" → resolved at runtime from environment configuration.

----

## TC-002: Successful login response matches the documented schema

**Tags:** @regression @contract @auth
**Technique:** Use Case Testing / contract validation — FR-1.2
**Isolation:** session-state

**Pre-conditions:**
- Valid credentials available; account not suspended.

**Request:** as TC-001.

**Expected Response:**
- **Status Code:** 200
- **Assertions:**
  - All documented fields present with correct types (token as non-empty string;
    any account/session metadata matches the contract observed in the first
    verified run and documented alongside this spec).
  - No undocumented sensitive fields (e.g. password hash) in the body.

**Test Data Setup:**
- "Valid credentials" → from configuration.

----

## TC-003: Session token is accepted by an authenticated endpoint

**Tags:** @smoke @regression @integration @auth
**Technique:** Use Case Testing (main flow end-to-end) — FR-1.3
**Isolation:** session-state

**Pre-conditions:**
- A session token obtained via a successful login within its ~6 h validity.

**Request:**
- **Method:** GET
- **Path:** a lightweight authenticated endpoint (e.g. current-account/session info)
- **Headers:** `session-token: <token from login>`

**Expected Response:**
- **Status Code:** 200
- **Assertions:**
  - Authenticated request succeeds with the token — proves login *works*, not
    merely *responds*.
  - The same request without the token returns 401/403 (control assertion).

**Test Data Setup:**
- "A fresh session token" → resolved by the login flow at runtime.

----

## TC-004: Repeated valid logins behave consistently

**Tags:** @regression @auth @integration
**Technique:** Use Case Testing (repetition) — FR-1.4, FR-4.1
**Isolation:** session-state

**Pre-conditions:**
- Valid credentials available; rate budget allows two sequential logins.

**Request:** two sequential valid logins (paced by the rate limiter).

**Expected Response:**
- **Assertions:**
  - Both return 200 with a valid token.
  - Behavior is consistent (same status, same schema); a second login does not
    invalidate the ability to authenticate.
  - Record (not assert) whether the same or a new token is issued — documents
    session semantics.

----

## TC-005: Login with a non-existent username returns 400 without a token

**Tags:** @regression @negative @auth
**Technique:** Equivalence Partitioning (invalid class: unknown user) — FR-2.1
**Isolation:** stateless

**Pre-conditions:**
- A syntactically valid username that cannot exist (unique random suffix).

**Request:**
- **Method:** POST
- **Path:** `/bpapi/rest/security/session`
- **Headers:** Content-Type: application/json
- **Body:**
  ```json
  { "username": "<non-existent username>", "password": "<any syntactically valid password>" }
  ```

**Expected Response:**
- **Status Code:** 400 (or documented 4xx; never 5xx)
- **Assertions:**
  - No session token issued (no `session-token` in body, headers, or cookies).
  - Error body is a generic authentication failure — no hint that distinguishes
    "user not found" from "wrong password" (user-enumeration guard, FR-2.1).
  - The submitted password is not echoed (FR-3.3).

**Test Data Setup:**
- "Non-existent username" → generated at runtime with a random suffix so it can
  never collide with a real account.

----

## TC-006: Wrong password for the real account returns 400, then recovery login succeeds

**Tags:** @regression @negative @security @auth
**Technique:** Decision Table (valid user × invalid password) — FR-2.2; sequencing per TD-001 §3
**Isolation:** account-state (atomic unit — must not interleave with any other account-state operation)

**Pre-conditions:**
- Valid username from configuration; account not suspended.
- No other account-state test running (enforced by execution grouping).
- **Runs at most once per suite execution** (PRD-001 NFR-1).

**Steps (one atomic workflow):**
1. POST login with the real username and a deliberately wrong password.
2. Assert the failure response (below).
3. Immediately POST login with the real, correct credentials (recovery login).
4. Assert recovery succeeded — this resets the consecutive-failure counter.

**Expected Response:**
- **Step 2:** status 400 (or documented 4xx), no token, error body
  indistinguishable from the non-existent-user error of TC-005 (enumeration
  guard), password not echoed.
- **Step 4:** status 200 with a valid token. **If recovery fails, abort the whole
  run** (abort condition, Architecture Design §10).

**Test Data Setup:**
- "Wrong password" → correct password mutated at runtime (e.g. suffix appended);
  never a second real credential.

----

## TC-007: Login with missing username field returns 400

**Tags:** @regression @negative @contract @auth
**Technique:** Decision Table (field presence: absent × present) — FR-2.3
**Isolation:** stateless

**Request:**
- **Method:** POST, **Path:** `/bpapi/rest/security/session`
- **Headers:** Content-Type: application/json
- **Body:**
  ```json
  { "password": "<any syntactically valid password>" }
  ```

**Expected Response:**
- **Status Code:** 400 — never 5xx.
- **Assertions:** no token issued; error indicates a validation failure without
  leaking internals.

----

## TC-008: Login with missing password field returns 400

**Tags:** @regression @negative @contract @auth
**Technique:** Decision Table (field presence: present × absent) — FR-2.3
**Isolation:** stateless

**Request:** body contains only `username` (a non-existent synthetic one, so even
an unexpected lenient path cannot touch the real account).

**Expected Response:**
- **Status Code:** 400 — never 5xx; no token; no internals leaked.

----

## TC-009: Login with empty body or null fields returns 400

**Tags:** @regression @negative @contract @auth
**Technique:** Decision Table (absent × absent; null × null) — FR-2.3
**Isolation:** stateless

**Request variants (each asserted separately):**
- Empty JSON object `{}`.
- `{ "username": null, "password": null }`.

**Expected Response:**
- **Status Code:** 400 for each variant — never 5xx; no token.

----

## TC-010: Login with syntactically invalid JSON returns 400

**Tags:** @regression @negative @contract @auth
**Technique:** Error Guessing (malformed body) — FR-2.4
**Isolation:** stateless

**Request:**
- **Headers:** Content-Type: application/json
- **Body:** raw string `{"username": "x", ` (truncated/invalid JSON)

**Expected Response:**
- **Status Code:** 400 — never 5xx.
- **Assertions:** error response is well-formed; no stack trace or parser
  internals in the body.

----

## TC-011: Login with wrong field types returns 400

**Tags:** @regression @negative @contract @auth
**Technique:** Error Guessing (type confusion) — FR-2.4
**Isolation:** stateless

**Request variants:**
- `username` as number, `password` as valid-shaped string.
- `username` as object/array.
- `password` as number.

**Expected Response:**
- **Status Code:** 400 per variant — never 5xx; no token; no internals leaked.

----

## TC-012: Login with wrong Content-Type is rejected

**Tags:** @regression @negative @contract @auth
**Technique:** Error Guessing (protocol misuse) — FR-2.4
**Isolation:** stateless

**Request:**
- **Headers:** Content-Type: text/plain
- **Body:** a valid-shaped JSON string with synthetic non-existent credentials.

**Expected Response:**
- **Status Code:** 4xx (expected 400 or 415) — never 5xx; no token.

----

## TC-013: Wrong HTTP methods on the session URL are rejected

**Tags:** @regression @negative @contract @auth
**Technique:** Error Guessing (method misuse) — FR-2.5
**Isolation:** stateless

**Request variants:** GET, PUT, PATCH on `/bpapi/rest/security/session` with no
credentials in the payload. (DELETE is excluded: on this API, DELETE on the
session resource is the documented *logout* operation, not an invalid method.)

**Expected Response:**
- **Status Code:** 4xx per variant (expected 405; documented value recorded after
  first run) — never 5xx.
- **Assertions:** no session created; response does not expose an internal error.

----

## TC-014: Login with empty-string credentials returns 400

**Tags:** @regression @negative @boundary @auth
**Technique:** Boundary Value Analysis (length 0) — FR-3.1
**Isolation:** stateless

**Request variants:** `""` username with syntactically valid password; valid-shaped
synthetic username with `""` password; both empty.

**Expected Response:**
- **Status Code:** 400 per variant — never 5xx; no token.

----

## TC-015: Login with whitespace-padded credentials does not authenticate

**Tags:** @regression @negative @boundary @auth
**Technique:** Boundary Value Analysis (whitespace edges) — FR-3.1
**Isolation:** stateless

**Request:** synthetic non-existent username padded with leading/trailing spaces,
any syntactically valid password. (Deliberately not padded real credentials:
if the API trims input, a padded real username + wrong password would spend a
strike against the real account.)

**Expected Response:**
- **Status Code:** 400 — never 5xx; no token.
- **Assertions:** behavior is consistent between padded and unpadded variants of
  the same non-existent username (documents trimming semantics safely).

----

## TC-016: Login with very long credential values is rejected cleanly

**Tags:** @regression @negative @boundary @auth
**Technique:** Boundary Value Analysis (extreme length) — FR-3.1
**Isolation:** stateless

**Request variants:** username of ~1 000 and ~10 000 characters (synthetic);
password of the same magnitudes.

**Expected Response:**
- **Status Code:** 4xx (400 or 413) per variant — never 5xx, no timeout, no
  connection reset.
- **Assertions:** response time stays within the client timeout (long input must
  not degrade the endpoint).

----

## TC-017: Login with unicode and special characters is handled cleanly

**Tags:** @regression @negative @boundary @auth
**Technique:** Error Guessing (encoding) — FR-3.1
**Isolation:** stateless

**Request variants:** synthetic usernames containing multibyte unicode (e.g.
CJK, emoji), combining characters, and JSON-escaped control characters.

**Expected Response:**
- **Status Code:** 400 per variant — never 5xx.
- **Assertions:** response is valid JSON; no encoding artifacts or mojibake in
  the error body.

----

## TC-018: Injection-style payloads are rejected without leaking internals

**Tags:** @regression @negative @security @auth
**Technique:** Error Guessing (security inputs) — FR-3.2
**Isolation:** stateless

**Request variants (synthetic username and/or password containing):**
- SQL-style: `' OR '1'='1`, `admin'--`
- JSON/structure-breaking: embedded quotes, `{"$gt": ""}`-style operators
- Path/template style: `../../`, `{{7*7}}`

**Expected Response:**
- **Status Code:** 4xx per variant — never 5xx.
- **Assertions:**
  - No session token issued for any variant.
  - Error body contains no stack traces, SQL fragments, framework names, or
    other internals (FR-3.2).
  - Submitted payload (including password field) is not echoed back (FR-3.3).

----

## TC-019: Error responses never echo the submitted password

**Tags:** @regression @security @auth
**Technique:** Checklist-Based (cross-cutting security assertion) — FR-3.3
**Isolation:** stateless

**Pre-conditions:**
- Executed against the responses of the negative cases (TC-005, TC-007–TC-018)
  using a unique, recognizable synthetic password marker.

**Expected Response:**
- **Assertions:** the marker value never appears in any response body, header,
  or redirect of any negative case. (Implemented as a shared assertion applied
  to every negative response rather than a separate API call — zero extra rate
  budget.)

----

## TC-020: Identical invalid requests get consistent responses

**Tags:** @regression @auth @contract
**Technique:** Repetition / reliability observation — FR-4.1
**Isolation:** stateless

**Request:** the same non-existent-username request (as TC-005) issued 3 times,
paced by the rate limiter.

**Expected Response:**
- **Assertions:** all 3 responses have the same status code and the same error
  body shape — the endpoint is deterministic for identical input.

----

## TC-021: Account is suspended after 3 consecutive failed logins — DOCUMENTED, NOT AUTOMATED

**Tags:** @wip @negative @security @auth
**Technique:** State Transition (failure counter) — PRD-001 §3.2
**Isolation:** account-state (destructive)

**Why not automated:** executing this suspends the shared account and blocks the
entire suite and other users of the account. Expected behavior (3 consecutive
failures → suspension; successful login resets the counter) is documented here
and verified at most once, manually, in a controlled way with a recovery path
agreed beforehand.

----

## TC-022: IP is blocked after more than 25 login attempts per minute — DOCUMENTED, NOT AUTOMATED

**Tags:** @wip @negative @performance @auth
**Technique:** State Transition (rate threshold) — PRD-001 §3.2
**Isolation:** environment-state (destructive)

**Why not automated:** verifying the threshold requires deliberately exceeding it,
blocking the runner's IP for an unknown duration. The suite instead *respects*
the limit by design (cross-process rate limiter, ADR-004); the block behavior is
documented as a manual, one-off observation only.

----

## TC-023: Session token expires after ~6 hours — DEFERRED

**Tags:** @wip @auth @integration
**Technique:** State Transition (session lifetime) — documented contract §3.1
**Isolation:** session-state

**Why deferred:** blackbox testing cannot manipulate server time, and a 6-hour
wall-clock wait is impractical in regression. Deferred until a practical
verification path exists (e.g. a long-running nightly job); token *validity* is
covered by TC-003.
