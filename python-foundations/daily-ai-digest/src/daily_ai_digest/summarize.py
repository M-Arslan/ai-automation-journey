"""LLM summarization using Anthropic Claude.

Two modes:
- summarize_structured: returns a validated Summary Pydantic object via tool use
- summarize_streaming:   yields text chunks as they arrive (free-text demo)
"""

from collections.abc import Iterator
from anthropic import Anthropic
from daily_ai_digest.config import ANTHROPIC_API_KEY, require
from daily_ai_digest.models import Summary, SummaryFields

# Module-level client — instantiated once, reused forever.
# The Anthropic SDK manages connection pooling internally; reusing the
# client is significantly faster than creating one per call.
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Lazy-init the Anthropic client."""
    global _client
    if _client is None:
        _client = Anthropic(api_key=require("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY))
    return _client


SYSTEM_PROMPT = (
    "You are a tech news editor. Given a Hacker News story, produce a concise "
    "structured summary by calling the submit_summary tool. Be factual and "
    "neutral; avoid hype and clickbait."
)


def summarize_structured(
    text: str,
    story_id: int,
    model: str = "claude-haiku-4-5",
) -> Summary:
    """Summarize via Anthropic tool use, returning a validated Summary."""
    client = _get_client()

    # Pydantic gives us a JSON schema for free.
    schema = SummaryFields.model_json_schema()

    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        tools=[
            {
                "name": "submit_summary",
                "description": "Submit your structured summary of the story.",
                "input_schema": schema,
            }
        ],
        # Force the model to call this specific tool. Without this, the model
        # might just respond with text and skip the tool entirely.
        tool_choice={"type": "tool", "name": "submit_summary"},
        messages=[{"role": "user", "content": text}],
    )

    # The response.content is a list of blocks. We expect one tool_use block.
    print(f"Model response blocks: {[b.type for b in response.content]}")
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_summary":
            # block.input is a dict — Anthropic already validated it against
            # our schema, but we re-validate through Pydantic for type safety.
            fields = SummaryFields.model_validate(block.input)
            return Summary(story_id=story_id, **fields.model_dump())

    raise RuntimeError(
        "Model did not produce a submit_summary tool_use block. "
        f"Got blocks: {[b.type for b in response.content]}"
    )

def summarize_streaming(
    text: str,
    model: str = "claude-haiku-4-5",
) -> Iterator[str]:
    """Yield free-text summary chunks as they arrive.

    NOTE: streaming and structured tool output don't combine cleanly. For
    real production use, prefer `summarize_structured` and accept the small
    latency. This function exists to demonstrate the streaming API.
    """
    client = _get_client()

    with client.messages.stream(
        model=model,
        max_tokens=200,
        system="You are a tech news editor. Summarize in 2 crisp sentences.",
        messages=[{"role": "user", "content": text}],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk


if __name__ == "__main__":
    import asyncio
    import time

    from daily_ai_digest.fetch_async import fetch_top_stories

    async def main():
        print("Fetching one HN story...\n")
        stories = await fetch_top_stories(limit=1)
        story = stories[0]
        prompt_text = (
            f"Title: {story.title}\nURL: {story.url}\nScore: {story.score}"
        )

        print(f"Story: {story.title}")
        print(f"  ({story.score} points, by {story.author})\n")

        # --- Structured output ---
        print("--- Structured (tool use) ---")
        start = time.perf_counter()
        summary = summarize_structured(prompt_text, story_id=story.id)
        elapsed = time.perf_counter() - start

        print(f"Headline: {summary.headline}")
        print("Key points:")
        for point in summary.key_points:
            print(f"  - {point}")
        print(f"Sentiment: {summary.sentiment}")
        print(f"Type: {type(summary).__name__}")
        print(f"  [{elapsed:.2f}s]\n")

        # --- Streaming demo ---
        print("--- Streaming (free text) ---")
        start = time.perf_counter()
        for chunk in summarize_streaming(prompt_text):
            print(chunk, end="", flush=True)
        elapsed = time.perf_counter() - start
        print(f"\n  [{elapsed:.2f}s]")

    asyncio.run(main())