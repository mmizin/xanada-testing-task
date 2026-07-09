"""Runtime generators for synthetic test data used by negative authentication scenarios.

Per TD-001 §5: non-existent usernames are the default vehicle for
negative-credential cases, so failed logins never spend one of the real
account's three strikes. ``non_existent_username()`` mints a fresh,
never-before-used value per call — a UUID suffix rules out both a collision
with any real username and a collision between parallel test workers.

``VALID_FORMAT_PASSWORD`` is a plain constant, not a generator: it never
varies, so a function call would only have implied randomness that isn't
there.
"""

from __future__ import annotations

import uuid


def non_existent_username(prefix: str = "qa-nonexistent") -> str:
    """A syntactically valid username guaranteed not to belong to any account."""
    return f"{prefix}-{uuid.uuid4().hex}"


VALID_FORMAT_PASSWORD = "Synthetic-P@ssw0rd-1"
"""A password shape acceptable to client-side validation, tied to no account."""
