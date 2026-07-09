---
name: skill-allure-pytest
description: "Guide for annotating pytest API tests with Allure reporting. Covers when to annotate, hierarchy decorators (epic/feature/story), test metadata (title/severity/owner), step wrappers, fixture titles, parametrize integration, and request/response attachments. Use before writing Allure annotations in pytest tests."
disable-model-invocation: false
---

You are a pytest + Allure reporting expert. Given a test file or feature area in `$ARGUMENTS`, apply Allure annotations that add genuine report value — no annotation for its own sake.

---

## When to Annotate (Decision Rule)

**Annotate** when any of these are true:
- The test belongs to a dashboard-filtered feature tree (epic/feature/story hierarchy needed)
- The test has multiple logical phases that benefit from step-level tracing in failure reports
- The severity/owner assignment is non-obvious and matters for triage prioritisation
- The test case has a corresponding ID in a test management system

**Skip Allure annotations** when:
- The test is a trivial single-assertion smoke check (one call + one assert)
- The test is a pure unit test with no external dependencies
- Adding steps would just wrap individual lines — not logical phases

---

## Setup

```bash
pip install allure-pytest
```

Run tests and generate a report:

```bash
pytest tests/ --alluredir allure-results
allure serve allure-results          # live server
# or
allure generate allure-results -o allure-report --clean
```

Disable auto-capture of stdout/stderr/logging when not needed:
```bash
pytest tests/ --alluredir allure-results --allure-no-capture
```

---

## Hierarchy Decorators

Use **behaviour-based** hierarchy for API tests (preferred):

```python
import allure

@allure.epic("<Domain>")
@allure.feature("<Capability>")
@allure.story("<Scenario Group>")
def test_example():
    ...
```

Mapping guide for this project:
- `@allure.epic` → top-level domain
- `@allure.feature` → sub-domain or capability
- `@allure.story` → specific scenario group (e.g. `Validation`, `Error Handling`)

Alternative **suite-based** hierarchy (use only when behaviour hierarchy doesn't fit):

```python
@allure.parent_suite("API Tests")
@allure.suite("<Domain>")
@allure.sub_suite("<Capability>")
def test_example():
    ...
```

---

## Test Metadata

```python
@allure.title("<Behaviour under test> returns <expected outcome>")
@allure.description("Verifies <what the test checks and why it matters>.")
@allure.severity(allure.severity_level.CRITICAL)   # BLOCKER | CRITICAL | NORMAL | MINOR | TRIVIAL
@allure.label("owner", "qa-team")
@allure.issue("QA-1234")
@allure.testcase("TC-001")
@allure.link("https://developers.matchbook.com/reference/login", name="API Docs")
def test_example():
    ...
```

**Severity guide:**
- `BLOCKER` — blocks release; core auth, payment flows
- `CRITICAL` — revenue-critical, major feature regression
- `NORMAL` — standard feature test (default for most API tests)
- `MINOR` — edge case, non-blocking UX issue
- `TRIVIAL` — cosmetic, low-priority negative case

---

## Steps

Use steps to mark **logical phases** of a test, not individual lines.

**Decorator on helper method (preferred for reusable steps):**

```python
class ApiSteps:
    @allure.step("Send request with params: {params}")
    def request(self, client, params: dict):
        return client.post("/endpoint", json=params)

    @allure.step("Assert response status is {expected_status}")
    def assert_status(self, response, expected_status: int):
        assert response.status_code == expected_status
```

**Context manager (for inline phases):**

```python
def test_example(api_client):
    with allure.step("Prepare request payload"):
        payload = {"field": "value"}

    with allure.step("Send POST /endpoint"):
        response = api_client.post("/endpoint", json=payload)

    with allure.step("Assert expected status and body"):
        assert response.status_code == 200
        assert response.json()["field"] == "value"
```

**Rules:**
- Group 3+ related lines into a step; never wrap a single line
- Step names must be self-explanatory without reading the test body
- Parameters in step names use `{param_name}` syntax (auto-resolved from method args)

---

## Fixtures with Allure Titles

Label fixtures so setup/teardown appears clearly in reports:

```python
import pytest
import allure

@pytest.fixture()
@allure.title("Create authenticated API client")
def auth_client(base_url, credentials):
    client = ApiClient(base_url, token=credentials["token"])
    yield client
    client.close()
```

---

## Parametrize Integration

Allure auto-captures `@pytest.mark.parametrize` values. Enhance readability for complex params:

```python
@pytest.mark.parametrize("value,expected_status", [
    ("valid_value", 200),
    ("", 400),
    ("X" * 256, 400),
])
def test_field_validation(api_client, value, expected_status):
    allure.dynamic.parameter("value", repr(value) if not value else value)
    ...
```

Use `allure.dynamic.parameter` when the raw parametrize value is unclear (e.g., empty string, long value).

---

## Attachments

Attach request/response bodies for failed API tests — this is the highest-value attachment use case:

```python
import json

def attach_request(method: str, url: str, body: dict | None = None):
    payload = {"method": method, "url": url, "body": body}
    allure.attach(
        json.dumps(payload, indent=2),
        name="Request",
        attachment_type=allure.attachment_type.JSON,
    )

def attach_response(response):
    allure.attach(
        response.text,
        name=f"Response {response.status_code}",
        attachment_type=allure.attachment_type.JSON,
    )
```

Attachment types available: `JSON`, `XML`, `HTML`, `TEXT`, `CSV`, `PNG`, `JPG`, `PDF`.

Attach only when diagnosis genuinely requires the body — not on every test.

---

## Dynamic Labels

Use `allure.dynamic.*` for labels that depend on runtime values (parametrised tests, conditional flows):

```python
def test_parametrised(api_client, field_name, field_value):
    allure.dynamic.title(f"Request with {field_name}={field_value!r}")
    allure.dynamic.severity(allure.severity_level.NORMAL)
    allure.dynamic.description(f"Verifies the endpoint handles {field_name} correctly.")
    ...
```

---

## Complete Example

```python
import allure
import pytest
from src.infra.http_client import ApiClient


@allure.epic("<Domain>")
@allure.feature("<Capability>")
@allure.story("<Scenario Group>")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("<Behaviour under test> returns 200 with expected body")
@allure.testcase("TC-001")
def test_example(api_client):
    with allure.step("Send request with valid payload"):
        payload = {"field": "value"}
        response = api_client.post("/endpoint", json=payload)

    with allure.step("Assert 200 OK"):
        assert response.status_code == 200

    with allure.step("Assert expected response body"):
        data = response.json()
        assert data.get("field") == "value"
```

---

## What NOT to Do

```python
# ❌ Steps wrapping single lines — no value
with allure.step("Call assert"):
    assert response.status_code == 200

# ❌ Annotating every trivial test
@allure.epic("<Domain>")
@allure.feature("Health")
@allure.story("Ping")
def test_health_check(api_client):
    assert api_client.get("/health").status_code == 200

# ❌ Allure title duplicating the function name
@allure.title("test_example")
def test_example():
    ...
```

---

## Key Constraints

- **Annotate intentionally** — every annotation should earn its place in the report
- **Hierarchy is for filtering** — if you won't filter by it on the dashboard, skip it
- **Steps are for failure diagnosis** — add them where a failing report needs context to diagnose the bug
- **Never annotate unit tests** — Allure adds overhead; unit tests run fast without it