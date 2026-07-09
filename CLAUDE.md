# CLAUDE.md

## Project

QA Automation Challenge (SDET position). The task is to write **blackbox regression
tests for a login endpoint** in Python.

This is an evaluation exercise. A perfect solution is not the goal — the reviewers are
looking for cues that reveal depth of understanding. **Comment and explain the intent
behind test cases and design choices** so the thought process is visible.

## The task

Write blackbox regression tests for the login endpoint covering:
- **Positive scenarios** (valid login)
- **Negative scenarios** (invalid credentials, missing fields, malformed input, etc.)
- **Edge cases** and any validations considered important
- How the endpoint behaves under different situations and whether it works reliably

## Endpoint under test

- **Documentation:** https://developers.matchbook.com/reference/login
- **Credentials:** Load from environment variables or `test_data/` (do not hardcode)
  - Username: `***********`
  - Password: `***********`

## Critical constraints (⚠️ affect test design)

These rate/lockout limits are enforced by the real system and can break test runs if
ignored. Design tests to respect them:

- **Account suspension:** the account is suspended after **three failed logins in a
  row**. Avoid chaining negative-credential tests against the real account without
  resetting; consider throttling, using clearly-invalid usernames, or isolating the
  "wrong password" case.
- **IP block:** the IP is blocked after **more than 25 login attempts per minute**.
  Keep total request rate under this threshold (pacing / rate limiting between tests).

## Project layout

- `src/` — helpers / API client code
- `tests/` — test suite

## Notes

- Language: Python.
- For open questions or feedback, the challenge instructions say to message the
  provided contact; when uncertain about scope or an approach, ask the user first.