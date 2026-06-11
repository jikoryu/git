"""Application configuration."""

import os


class Config:
    # Google Safe Browsing API key (optional — if not set, skips GSB check)
    GOOGLE_SAFE_BROWSING_KEY: str = os.environ.get(
        "GOOGLE_SAFE_BROWSING_KEY", ""
    )

    # Timeout for external HTTP requests
    REQUEST_TIMEOUT: int = 15


config = Config()
