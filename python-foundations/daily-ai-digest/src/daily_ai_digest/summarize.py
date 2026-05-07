"""LLM summarization using Anthropic Claude.

This is the "raw SDK" version; we'll wrap it in LangChain in Week 3.
"""

from anthropic import Anthropic

from daily_ai_digest.config import ANTHROPIC_API_KEY, require

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
    "You are a tech news editor. Summarize Hacker News stories in exactly "
    "two crisp sentences. First sentence: what the story is about. "
    "Second sentence: why it matters. No hype, no clickbait."
)


def summarize(text: str, model: str = "claude-haiku-4-5") -> str:
    """Summarize `text` with Claude. Returns the summary as a plain string."""
    client = _get_client()

    response = client.messages.create(
        model=model,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )

    # response.content is a list of content blocks. For plain-text responses
    # the first block is a TextBlock with a .text attribute.
    return response.content[0].text


if __name__ == "__main__":
    import asyncio
    import time

    from daily_ai_digest.fetch_async import fetch_top_stories

    async def main():
        print("Fetching one HN story to summarize...\n")
        stories = await fetch_top_stories(limit=1)
        story = stories[0]
        prompt_text = (
            f"Title: {story.title}\nURL: {story.url}\nScore: {story.score}"
        )

        print(f"Story: {story.title}")
        print(f"  ({story.score} points, by {story.author})\n")

        print("--- Claude (Haiku) ---")
        start = time.perf_counter()
        summary = summarize(prompt_text)
        elapsed = time.perf_counter() - start
        print(summary)
        print(f"\n  [{elapsed:.2f}s]")

    asyncio.run(main())