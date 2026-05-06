"""Centralized config — loads env vars once at import time."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Find the .env file at the project root (two levels up from this file:
# src/daily_ai_digest/config.py → src/daily_ai_digest/ → src/ → project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def require(name: str, value: str | None) -> str:
    """Fail loudly if a required env var is missing."""
    if not value:
        raise RuntimeError(
            f"Missing env var: {name}. "
            f"Copy .env.example to .env and fill in your keys."
        )
    return value