# ADR-001 — Feature-based Automation Architecture

- Status: Accepted
- Date: 2026-07-08
- Decision makers: QA / SDET

## Context

We are building an automation framework whose first feature is authentication
regression testing, but which must scale beyond a single feature (future areas:
account, betting, etc.). The top-level code organization determines how the
framework grows, who owns what, and how safely it can be changed.

## Considered options

### Option 1 — Technical layer structure

Organize code by technical role:

```
src/
├── clients/
├── models/
├── validators/
└── tests/
```

Problems:

- Feature logic becomes distributed across every layer — understanding or changing
  one feature means touching (and reading) many top-level directories.
- Ownership boundaries are unclear: every layer is shared by every feature, so
  every change is potentially cross-feature.
- Scales poorly: as APIs are added, layer directories grow into large shared
  modules ("helpers" sprawl) that everyone depends on and no one can safely change.

### Option 2 — Feature-based structure

Organize code by business feature, with technical layering inside each feature:

```
features/
└── authentication/
    ├── api/
    ├── models/
    ├── services/
    └── validators/
```

Cross-feature capabilities (HTTP transport, configuration, rate limiting,
reporting) live in a shared infrastructure package that features depend on — never
the reverse.

## Decision

Use the **feature-based structure** (Option 2).

Everything one feature needs lives in its package; new features are added as new
packages with the same internal shape. Shared infrastructure holds only
feature-agnostic capabilities.

## Consequences

Positive:

- Better scalability — adding a feature does not touch existing features.
- Clear feature ownership and natural review boundaries, mirroring how the API
  itself (and a real team) is organized.
- Easier maintenance — the blast radius of a change is one feature package or the
  explicitly shared infra.

Negative:

- Some concepts may be duplicated between features (e.g. similar validator
  patterns) before a shared abstraction is justified. We accept duplication until
  a pattern appears in at least two features, rather than pre-building shared
  layers.
