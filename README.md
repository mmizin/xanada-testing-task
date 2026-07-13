# Xanadu Testing Task — Login Endpoint Regression Suite

Blackbox regression tests for the Matchbook [login endpoint](https://developers.matchbook.com/reference/login),
written as a QA Automation Challenge (SDET position). The suite exercises
positive, negative, and edge-case scenarios against the real API while
respecting its account-lockout and IP rate-limit rules.

See `docs/product/` for the full design trail (PRD, ADRs, architecture,
test design) and `test-cases/api/authentication/` for the human-readable
test case spec and automation decisions behind what's implemented here.

## Project layout

```
src/
  features/authentication/   # login API client, response models, fixtures, assertions
  infra/                     # HTTP client, env config, cross-process rate limiter
  fixtures/                  # shared pytest fixtures (http client)
  utils/                     # test data generators
tests/
  authentication/
    behavior/      # request/response behavior: positive, negative, edge cases
    contract/       # response schema/contract checks
    integration/   # cross-cutting checks (session cookie, HTTP methods)
conftest.py         # composition root: settings + rate-limiter fixtures
docs/product/        # PRD, ADRs, architecture design, test design
test-cases/           # test case spec + automation-decision rationale
```

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- [Allure commandline](https://allurereport.org/docs/install/) to view HTML reports (`brew install allure` on macOS)

## Setup

```bash
cp .env.example .env
```

Fill in `.env` with the shared test account's credentials:

```
MATCHBOOK_USERNAME=...
MATCHBOOK_PASSWORD=...
```

Credentials are **never** hardcoded — `src/infra/config.py` loads them from
the environment (via `.env` locally, real env vars in CI) and fails fast if
they're missing. `.env` is git-ignored.

Install dependencies:

```bash
uv sync --extra dev
```

or with plain `pip`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## ⚠️ Account and rate-limit constraints

These are enforced by the real system, not by this test suite — see
`.env.example` and `src/infra/rate_limiter.py` for how the suite protects
against them:

- **Account suspension** after 3 consecutive failed logins on the shared
  account. Exactly one test (`test_login_wrong_password.py`, TC-006) is
  allowed to spend a strike, and it immediately follows up with a correct
  login to reset the counter.
- **IP block** after more than 25 login attempts/minute. A cross-process
  rate limiter (ADR-004) paces every request — including across
  `pytest-xdist` workers — to a shared budget (`RATE_LIMIT_MAX_PER_MINUTE`,
  default 20/min) via minimum inter-request spacing, not a bucket that lets
  a burst through.

Do not disable `RATE_LIMIT_ENABLED` or raise the limit above 25/min against
the real API.

## Running the tests

Run the full suite:

```bash
uv run pytest
```

Run a specific file or test:

```bash
uv run pytest tests/authentication/behavior/test_login_wrong_password.py
uv run pytest -k test_login_wrong_password
```

Run by marker (see `pyproject.toml` for the full marker list — `positive`,
`negative`, `edge_case`, `login`, `integration`, `slow`):

```bash
uv run pytest -m positive
uv run pytest -m "negative and login"
```

Run in parallel (pytest-xdist), safe by design (ADR-003 — the rate limiter
and account-state isolation hold across workers):

```bash
uv run pytest -n auto
```

Without `uv`, drop the `uv run` prefix (activate the venv first).

## Allure reporting

Every run writes raw results to `reports/allure-results/` automatically
(`--alluredir`, configured in `pyproject.toml`; the directory is cleaned at
the start of each run).

Generate and open an HTML report after a run:

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

Or serve directly from the raw results without a separate build step:

```bash
allure serve reports/allure-results
```

## Linting and type-checking

```bash
uv run black --check .
uv run isort --check-only .
uv run flake8
uv run mypy src tests
```

## Coverage

```bash
uv run pytest --cov
```

Coverage config (source paths, exclusions) lives in `pyproject.toml`
under `[tool.coverage.*]`.
