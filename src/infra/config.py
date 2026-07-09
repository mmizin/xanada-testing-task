"""Environment-driven configuration loading.

Per Architecture Design §9: environment variables are the single source for
environment-specific values (base URL, credentials). Loaded once, validated
eagerly so a misconfigured run fails before any API call is made, rather than
failing confusingly mid-suite on the first login attempt.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Matchbook's own base URL (PRD-001 §"Endpoint under test") — a sensible
# default since it isn't secret, but still overridable for a staging target.
_DEFAULT_BASE_URL = "https://api.matchbook.com"


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved configuration for a test run."""

    base_url: str
    username: str
    password: str

    @classmethod
    def load(cls) -> "Settings":
        """Read settings from the environment, failing fast if incomplete.

        Calls ``load_dotenv()`` first: on a developer machine this populates
        ``os.environ`` from a git-ignored ``.env`` file (see ``.env.example``);
        in CI, where real env vars are already injected, the call is a no-op.
        Credentials have no default on purpose (PRD-001 NFR-4) — an empty or
        missing value must raise, never silently proceed with an empty string.
        """
        load_dotenv()

        base_url = os.environ.get("MATCHBOOK_BASE_URL", _DEFAULT_BASE_URL)
        username = os.environ.get("MATCHBOOK_USERNAME")
        password = os.environ.get("MATCHBOOK_PASSWORD")

        missing = [
            name
            for name, value in (
                ("MATCHBOOK_USERNAME", username),
                ("MATCHBOOK_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required environment variable(s): "
                f"{', '.join(missing)}. Set them in the environment or in a "
                "local .env file (see .env.example)."
            )

        return cls(base_url=base_url, username=username, password=password)

    def __repr__(self) -> str:
        # Defensive redaction (Architecture Design §9): even though nothing
        # currently logs a Settings instance, this ensures a stray print/log
        # or Allure attachment can never leak the password.
        return f"Settings(base_url={self.base_url!r}, username={self.username!r}, password='***')"