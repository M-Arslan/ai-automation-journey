"""Compare sync vs async fetcher head-to-head."""

import asyncio
import time

from daily_ai_digest.fetch import fetch_top_stories as fetch_sync
from daily_ai_digest.fetch_async import fetch_top_stories as fetch_async

LIMIT = 30


def time_sync():
    start = time.perf_counter()
    stories = fetch_sync(limit=LIMIT)
    return len(stories), time.perf_counter() - start


async def time_async():
    start = time.perf_counter()
    stories = await fetch_async(limit=LIMIT)
    return len(stories), time.perf_counter() - start


def main():
    print(f"Fetching top {LIMIT} stories from HN, two ways...\n")

    sync_count, sync_elapsed = time_sync()
    print(f"  sync : {sync_count} stories in {sync_elapsed:.2f}s")

    async_count, async_elapsed = asyncio.run(time_async())
    print(f"  async: {async_count} stories in {async_elapsed:.2f}s")

    print(f"\nSpeedup: {sync_elapsed / async_elapsed:.1f}x faster")


if __name__ == "__main__":
    main()