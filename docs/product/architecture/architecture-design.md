# Architecture Design — Login Regression Testing System

- **Status:** Draft
- **Owner:** QA / SDET (Mykola Mizin)
- **Related docs:** [Idea Brief](../01-idea-brief.md) ·
  [PRD-001 — Authentication](../prd/PRD-001-authentication.md) ·
  [TD-001 — Test Design](../test-design/TD-001-authentication.md)

> Scope of this document: **how** the automated regression testing system is
> designed and structured to satisfy PRD-001. Specific decisions with meaningful
> alternatives are (or will be) captured as ADRs; this document records the overall
> shape. It stays at the architecture level — no class names, code snippets, or
> file-level detail.

## 1. Architecture overview

### Purpose

The system is an automated blackbox regression suite for the Matchbook login
endpoint. The "product" is the testing system itself: its job is to detect
authentication regressions reliably while being safe to run repeatedly — and in
parallel — against a live API that enforces account-suspension and IP-block limits.

### Scope

- In scope: the authentication feature (login endpoint), the infrastructure needed
  to test it safely (rate limiting, configuration, secrets handling), and evidence
  reporting.
- Out of scope: load testing, other Matchbook features (beyond supporting calls
  such as token validation), UI testing.

### Main design goals

1. **Safety first** — the architecture must make it structurally hard to violate
   the lockout/rate limits (PRD-001 NFR-1/NFR-2), not rely on test authors
   remembering to be careful.
2. **Parallel by design** — the system runs in parallel while protecting stateful
   scenarios; safety is achieved through isolation rules, not by disabling
   parallelism.
3. **Traceability** — each test maps to a designed case; each result carries the
   evidence needed to diagnose it without re-running (PRD-001 NFR-5).
4. **Extensibility** — adding a second feature (e.g. account, betting) must not
   require touching the authentication feature; shared concerns live in
   infrastructure.
5. **Determinism** — tests are independent and order-safe; shared state is managed
   explicitly (PRD-001 NFR-3).

## 2. Architecture principles

### Why feature-based architecture

The codebase is organized around **business features** (authentication first)
rather than technical layers at the top level. Rationale:

- Regression suites grow feature by feature; a feature-based layout keeps
  everything needed to understand and change one feature's tests — clients, models,
  services, validators, fixtures, test data — in one place.
- It mirrors how the API itself is organized (and how a real team would own areas),
  so ownership and review boundaries are natural.
- It prevents the common failure mode of layer-based test frameworks: giant shared
  "helpers" modules that every feature depends on and no one can safely change.

(Formal decision record: ADR-001 "Feature-based architecture", planned.)

### Separation of concerns

Each layer has one reason to change:

- **Tests** express expected behavior (the *what* from PRD/TD) and contain no HTTP
  or transport detail.
- **Feature services** encapsulate feature-level workflows and safety choreography
  (e.g. "wrong password then recovery login" as one unit).
- **API clients** know endpoints, payload shapes, and headers — nothing about test
  expectations.
- **Infrastructure** provides cross-feature capabilities: HTTP transport,
  configuration, rate limiting, reporting hooks.

### Maintainability and scalability

- New features are added as new packages under `features/` with the same internal
  shape, so the structure is self-documenting.
- Safety controls (rate limiter, pacing) are applied at the transport level, so no
  new test can accidentally bypass them.
- Test data and validators are **colocated with the feature that owns them**; only
  genuinely cross-feature data and utilities live in shared modules.

## 3. High-level architecture

Primary request path:

```
Tests (pytest)
   ↓  express scenarios & assertions
Feature services (authentication)
   ↓  feature workflows, safety choreography
API clients (authentication)
   ↓  endpoint knowledge: URLs, payloads, headers
HTTP client (httpx, via infra)
   ↓  transport + global rate limiting
Matchbook API
```

Supporting components (cross-cutting):

```
Fixtures ──────────► wire configuration, clients, services into tests
Configuration ─────► environment-driven settings & credentials
Rate limiter ──────► shared cross-process pacing at the transport layer
Allure reporting ──► evidence capture (redacted) attached to every result
```

Key property: **every** outbound login request — regardless of which test, worker,
or service issues it — passes through the same rate-limited HTTP layer. Safety is a
property of the architecture, not of individual tests.

## 4. Test isolation strategy

Parallel execution against a stateful external system is only safe if the
architecture is explicit about **which tests touch which state**. Tests are
therefore categorized by their interaction with external state, and the category —
not the test author's judgment at scheduling time — determines how a test may be
executed.

### Stateless tests

- **Examples:** non-existent username, malformed payload, missing fields, invalid
  HTTP method.
- **Characteristics:** no account mutation; the API treats each request
  independently.
- **Execution:** fully parallelizable — safe on any pytest-xdist worker at any
  time (subject only to the global rate budget).

### Session-state tests

- **Examples:** successful login, token validation.
- **Characteristics:** create authentication sessions on the server. A successful
  login is **not** assumed side-effect-free — it produces server-side session
  state and may interact with limits we don't fully know (e.g. concurrent-session
  policies).
- **Execution:** may run in parallel **with proper isolation** — each test owns
  its session lifecycle and never shares or assumes another test's session;
  controlled execution keeps concurrent session creation bounded.

### Account-state tests

- **Examples:** wrong password followed by recovery login.
- **Characteristics:** mutate the real account's authentication state (the
  consecutive-failure counter). Order and adjacency matter.
- **Execution:** atomic workflow — the whole sequence executes as one indivisible
  unit and **cannot interleave with any other account-state operation**. These
  tests are serialized among themselves via execution grouping.

This categorization is an architectural contract: every new test must declare its
category, and the execution layer enforces the corresponding isolation rule.

## 5. Parallel execution strategy

The system supports parallel execution (pytest-xdist) while protecting stateful
scenarios. Parallelism is intentional: the goal is a regression system that stays
fast as it grows, with safety enforced by shared controls rather than by running
everything sequentially.

```
pytest-xdist workers

   Worker 1        Worker 2        Worker 3
      │               │               │
      └───────────────┼───────────────┘
                      ▼
        Shared safety controls
        - cross-process rate limiter (one global budget)
        - test isolation rules (§4 categories)
        - execution grouping (account-state atomicity)
                      ▼
                Matchbook API
```

How the isolation categories map onto workers:

- **Stateless tests** are distributed freely across all workers.
- **Session-state tests** run in parallel but isolated: each owns its session
  lifecycle; no cross-test session sharing.
- **Account-state tests** are pinned to an execution group that guarantees
  atomicity — no other account-state operation runs while the wrong-password →
  recovery-login unit is in flight.
- **Rate limiting is global across workers**: the workers share one request
  budget, so adding workers never increases pressure on the API's 25/minute IP
  limit. Note the corollary: parallel speedup applies to test overhead and
  non-login work; total login throughput is bounded by the shared budget by
  design.

(Formal decision record: ADR-003 "Parallel execution strategy for stateful API
tests", planned.)

## 6. Project structure

```
src/
 ├── features/    # feature packages; each owns its clients, models, services,
 │                # validators, fixtures, and test data
 ├── fixtures/    # cross-feature pytest fixtures (session-scoped config,
 │                # HTTP client, reporting hooks)
 ├── infra/       # infrastructure: HTTP transport wrapper, rate limiter,
 │                # configuration loading, secrets masking
 ├── test_data/   # cross-feature test data ONLY (feature-specific data lives
 │                # inside the owning feature)
 └── utils/       # small generic helpers with no domain knowledge

tests/            # test suites, mirroring the feature structure; contain only
                  # scenario logic and assertions
```

### Feature ownership boundaries

```
src/

features/
 │
 ├── authentication
 │      │
 │      ├── api            # endpoint clients
 │      ├── models         # request/response representations
 │      ├── services       # feature workflows & safety choreography
 │      ├── validators     # feature-specific assertions
 │      ├── fixtures       # feature-specific fixtures
 │      └── test_data      # feature-owned test data
 │
 └── (future features: account, betting, …) — same internal shape

infra/
 │
 ├── http                  # transport wrapper
 ├── config                # configuration & secrets loading
 ├── reporting             # evidence capture & redaction
 └── rate limiting         # shared cross-process limiter
```

Everything a feature needs lives inside its package; `infra/` provides only
capabilities that are feature-agnostic by nature. If a piece of data or logic is
used by exactly one feature, it belongs to that feature.

## 7. Component design

| Component | Responsibility |
|---|---|
| **HTTP client** (infra) | Single wrapper over httpx used by all API clients. Owns base URL, timeouts, default headers, and enforces the global rate limiter on every request. The only component that talks to the network. |
| **Authentication API client** | Knows the login endpoint contract: how to build a login request (including deliberately malformed variants for negative tests) and return the raw response untouched — no assertions. |
| **Authentication service** | Feature-level workflows composed from client calls: obtain a valid session, verify a token against an authenticated endpoint, execute the atomic wrong-password → recovery-login sequence, trigger abort-fast when a supposedly valid login fails. |
| **Response validators** | Reusable assertion units for status codes, response schema, error-body shape, and security properties (password never echoed, no user-enumeration hints). Keep expectations consistent across tests. |
| **Fixtures** | Compose the system for tests: load configuration once per session, provide the shared HTTP client and services, manage session/token lifecycle, and guarantee safety controls are active before any test runs. |
| **Configuration management** | Environment-driven settings (base URL, credentials, rate budget, timeouts). One loading point; validated at startup so misconfiguration fails fast, before any API call. |
| **Allure reporting** | Attaches request/response evidence to every test result, with secrets redacted at the capture point (so redaction cannot be forgotten per test). Provides the epic/feature/story hierarchy for navigation. |

## 8. Test execution flow

Lifecycle of a run:

```
pytest start
   ↓
load & validate configuration        (fail fast on missing/invalid settings)
   ↓
initialize session-scoped fixtures   (HTTP client, services, reporting hooks)
   ↓
apply safety controls                (cross-process rate limiter armed;
                                      isolation rules & execution groups active)
   ↓  — per test, on any worker —
execute API call via service/client  (paced by the shared rate limiter)
   ↓
validate response                    (validators: status, schema, security)
   ↓
attach evidence to Allure            (redacted request/response, verdict)
   ↓
teardown                             (session hygiene; abort-fast state checked)
```

Failure handling: if a login that should succeed fails, the run aborts fast instead
of retrying — retry storms are exactly how the shared account gets suspended.

## 9. Configuration and secrets management

- **Environment variables** are the single source for environment-specific values:
  base URL, username, password, rate budget. Local development may use a dotenv
  file that is git-ignored; CI injects real environment variables.
- **Credentials are never hard-coded** in tests, services, or committed files
  (PRD-001 NFR-4). The repository contains no secrets; documentation references
  the credential *names*, not values, once implementation starts.
- **Password masking is centralized**: the evidence-capture layer redacts secret
  values before anything reaches logs or Allure attachments. Because redaction
  happens at capture time in one place, individual tests cannot leak the password
  by omission.
- **Reports and logs are treated as published artifacts**: anything attached to a
  report is assumed shareable, hence redaction is mandatory, not best-effort.

## 10. Safety mechanisms

These implement PRD-001 NFR-1/NFR-2 and TD-001 §3 at the architecture level:

- **Global rate limiting** — a **shared cross-process rate limiter** guards the
  transport layer; every login request from every worker is paced against one
  global budget, staying well under the 25 requests/minute IP limit (target
  ≤ ~15/min). No code path can reach the API around it. The concrete sharing
  mechanism (file-lock token bucket, Redis-based limiter, or another shared
  medium) is an implementation decision deferred to ADR-004.
- **Test isolation enforcement** — the §4 categories are enforced by the execution
  layer: stateless tests scheduled freely, session-state tests isolated per test,
  account-state tests executed atomically via grouping.
- **Failed-login protection** — negative-credential tests default to non-existent
  usernames so failures never accrue against the real account. At most one failed
  attempt with the real username occurs per run.
- **Recovery login strategy** — the single wrong-password test is one atomic unit:
  wrong attempt → recovery login → success asserted. The failure counter is reset
  within the same unit boundary, and grouping guarantees no other account-state
  operation runs in between.
- **Abort conditions** — the run aborts immediately when: a valid-credentials login
  unexpectedly fails (possible suspension), the API signals rate limiting, or the
  recovery login fails. Remaining tests are skipped rather than allowed to dig the
  hole deeper.

## 11. Technology decisions

| Area | Choice | Architecture-level rationale |
|---|---|---|
| Language | Python | Challenge requirement; standard SDET ecosystem |
| Test framework | pytest | Fixture model fits the session/safety lifecycle; parametrization maps cleanly to designed test cases |
| HTTP client | httpx | Modern client with first-class timeout control and event hooks, which suit centralized rate limiting and evidence capture (ADR-002, planned) |
| Parallelism | pytest-xdist | Parallel execution with shared safety controls; isolation strategy in §4–§5 (ADR-003, planned) |
| Reporting | Allure | Hierarchical reports with per-test attachments satisfy the evidence/diagnosability requirement (PRD-001 NFR-5) |

## 12. Planned follow-up documents

- ADR-001 Feature-based architecture
- ADR-002 HTTP client selection (httpx)
- ADR-003 Parallel execution strategy for stateful API tests
- ADR-004 Rate limiter design (cross-process sharing mechanism)
- Test Design continuation: concrete case inventory and automation decisions
  (TD-001 §4).
