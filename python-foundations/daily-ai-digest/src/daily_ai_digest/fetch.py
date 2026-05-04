"""Synchronous Hacker News fetcher.

Demonstrates basic httpx usage:
- Reusing a Client (connection pooling)
- Setting timeouts
- Validating responses with raise_for_status
- Parsing JSON into Pydantic models
"""

import httpx

from daily_ai_digest.models import HackerNewsStory

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def fetch_top_story_ids(client: httpx.Client, limit: int = 30) -> list[int]:
    """Fetch the IDs of the top N HN stories.

    The /topstories endpoint returns up to 500 IDs; we slice to `limit`.
    """
    response = client.get(f"{HN_API_BASE}/topstories.json")
    response.raise_for_status()  # raise httpx.HTTPStatusError on 4xx/5xx
    all_ids = response.json()
    return all_ids[:limit]


def fetch_item(client: httpx.Client, item_id: int) -> dict | None:
    """Fetch a single HN item by ID. Returns None for missing items."""
    response = client.get(f"{HN_API_BASE}/item/{item_id}.json")
    response.raise_for_status()
    data = response.json()
    # HN returns `null` (None in Python) for deleted/missing items
    return data


def fetch_top_stories(limit: int = 30) -> list[HackerNewsStory]:
    """Fetch the top `limit` stories, validated as Pydantic models.

    Skips non-story items (jobs, polls, etc.) and items that fail validation.
    """
    stories: list[HackerNewsStory] = []

    # `with httpx.Client(...)` reuses a TCP connection across all calls — much
    # faster than opening a new connection for every request.
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        ids = fetch_top_story_ids(client, limit=limit)

        for item_id in ids:
            data = fetch_item(client, item_id)

            if data is None:
                continue  # deleted item

            if data.get("type") != "story":
                continue  # job, poll, etc.

            try:
                story = HackerNewsStory.model_validate(data)
                stories.append(story)
            except Exception as e:
                # Some "stories" are missing fields (e.g. score). Log and skip.
                print(f"  [skip] Item {item_id} failed validation: {e}")

    return stories


if __name__ == "__main__":
    import time

    start = time.perf_counter()
    stories = fetch_top_stories(limit=30)
    elapsed = time.perf_counter() - start

    print(f"\nFetched {len(stories)} stories in {elapsed:.2f}s\n")
    for story in stories[:5]:
        print(f"  [{story.score}] {story.title}")
        print(f"         by {story.author} — {story.url}")
        print()

    print(f"... and {len(stories) - 5} more")