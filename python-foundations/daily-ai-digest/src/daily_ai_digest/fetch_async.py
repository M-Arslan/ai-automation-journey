"""Asynchronous Hacker News fetcher.

Same job as fetch.py, but uses httpx.AsyncClient + asyncio.gather to
fetch all stories concurrently instead of one at a time.
"""

import asyncio

import httpx

from daily_ai_digest.models import HackerNewsStory

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=15.0)


async def fetch_top_story_ids(client: httpx.AsyncClient, limit: int = 30) -> list[int]:
    """Fetch the IDs of the top N HN stories."""
    response = await client.get(f"{HN_API_BASE}/topstories.json")
    response.raise_for_status()
    return response.json()[:limit]


async def fetch_item(client: httpx.AsyncClient, item_id: int) -> dict | None:
    """Fetch a single HN item by ID."""
    response = await client.get(f"{HN_API_BASE}/item/{item_id}.json")
    response.raise_for_status()
    return response.json()

async def fetch_weather_data(client:httpx.AsyncClient, city:str) -> dict:
    """Fetch weather data for a given city."""
    api_key = "1a309832f00b7329b7d07bcaa506635a"  # Replace with your actual API key from OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = await client.get(url)
    response.raise_for_status()
    return response.json()  

async def weather_gather(client:httpx.AsyncClient, city:str):
    """Fetch weather data for multiple cities concurrently."""
    cities = ["New York", "London", "Tokyo", "Sydney", "Paris"]
    tasks = [fetch_weather_data(client, city) for city in cities]
    weather_data = await asyncio.gather(*tasks)
    return weather_data

    

async def fetch_top_stories(limit: int = 30) -> list[HackerNewsStory]:
    """Fetch the top stories concurrently."""
    stories: list[HackerNewsStory] = []

    # `async with` — note the `async` prefix. AsyncClient must be set up and
    # torn down asynchronously because it manages async resources internally.
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        # Step 1: get the IDs (single sequential call)
        ids = await fetch_top_story_ids(client, limit=limit)

        # Step 2: fetch all items concurrently.
        # asyncio.gather schedules all coroutines on the event loop at once
        # and waits for all of them to finish. The list comprehension just
        # builds the list of coroutine objects; nothing runs until gather().
        items = await asyncio.gather(
            *[fetch_item(client, item_id) for item_id in ids]
        )

    # Step 3: validate sequentially (CPU work, no need for async here)
    for item_id, data in zip(ids, items):
        if data is None or data.get("type") != "story":
            continue
        try:
            stories.append(HackerNewsStory.model_validate(data))
        except Exception as e:
            print(f"  [skip] Item {item_id} failed validation: {e}")

    return stories


if __name__ == "__main__":
    import time

    async def main():
        start = time.perf_counter()
        stories = await fetch_top_stories(limit=100)
        elapsed = time.perf_counter() - start

        # print(f"\nFetched {len(stories)} stories in {elapsed:.2f}s\n")
        # for story in stories[:5]:
        #     print(f"  [{story.score:>4}] {story.title}")
        #     print(f"         by {story.author} — {story.url}")
        #     print()
        # print(f"... and {len(stories) - 5} more")

        print(f"\\n weather data for multiple cities concurrently...\\n")
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            start = time.perf_counter()
            weather_data = await weather_gather(client, city="")
            for data in weather_data:
                print(f"City: {data['name']}, Weather: {data['weather'][0]['description']}, Temperature: {data['main']['temp']}K")
            elapsed = time.perf_counter() - start
            print(f"\\nFetched weather data for {len(weather_data)} cities in {elapsed:.2f}s\\n")

    asyncio.run(main())