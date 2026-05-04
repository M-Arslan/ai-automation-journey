"""Pydantic models for the Daily AI Digest project.

These models define the data shapes we'll work with:
- HackerNewsStory: a single story fetched from HN's API
- Summary: an LLM-generated summary of one story
- DigestConfig: configuration for a digest run
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class HackerNewsStory(BaseModel):
    """A single story fetched from the Hacker News Firebase API.

    HN's API returns more fields than we use; we only declare the ones we care
    about. Pydantic ignores unknown fields by default, which is convenient.
    """

    id: int
    title: str
    # `by` is HN's author field. We rename it on our side using `alias`.
    author: str = Field(alias="by")
    score: int
    # `url` is missing for "Ask HN" / "Show HN" text posts. Use `| None`
    # (the modern Python 3.10+ syntax) instead of `Optional[HttpUrl]`.
    url: HttpUrl | None = None
    # HN's `time` field is a Unix timestamp (int). We can declare it as
    # datetime and Pydantic will coerce it for us.
    time: datetime
    # `descendants` is HN's comment count. Default to 0 if missing.
    descendants: int = 0


class Summary(BaseModel):
    """An LLM-generated summary of a single HN story.

    This is the structured output shape we'll ask Claude/GPT to produce.
    Forcing structured output (rather than free-text) is one of the most
    important habits in AI engineering.
    """

    headline: str = Field(
        ..., description="A 5-10 word punchy rewrite of the story's title."
    )
    key_points: list[str] = Field(
        ..., description="2-4 bullet points capturing the substance.", min_length=2, max_length=4
    )
    sentiment: Literal["positive", "neutral", "negative"]
    # Source story ID so we can link the summary back to the original.
    story_id: int


class DigestConfig(BaseModel):
    """Runtime configuration for one digest run.

    Lives in code (with sane defaults) but can be overridden via CLI flags
    or environment variables when we wire up the CLI on Day 10.
    """

    story_count: int = Field(default=10, ge=1, le=50)
    llm_provider: Literal["openai", "anthropic"] = "anthropic"
    output_path: str = "digest.md"
    # Concurrency limit for parallel LLM calls (avoid rate limits).
    max_concurrent_llm_calls: int = Field(default=5, ge=1, le=20)