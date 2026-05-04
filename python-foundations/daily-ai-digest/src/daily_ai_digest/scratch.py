# """Quick smoke test for our models. Run with: uv run python scratch.py"""

# from datetime import datetime
# from daily_ai_digest.models import DigestConfig, HackerNewsStory, Summary

# # Test 1: HackerNewsStory parsing real HN API data
# raw_hn = {
#     "id": 39512345,
#     "title": "Show HN: My new project",
#     "by": "arslan",  # note: HN uses `by`, our model uses `author` via alias
#     "score": 142,
#     "url": "https://example.com/post",
#     "time": 1740000000,  # Unix timestamp
#     "descendants": 23,
#     # HN returns a bunch of other fields we ignore — Pydantic doesn't care
#     "type": "story",
#     "kids": [1, 2, 3],
# }
# story = HackerNewsStory.model_validate(raw_hn)
# print(f"Story: {story.title} by {story.author} ({story.score} points)")
# print(f"  URL is a real {type(story.url).__name__}: {story.url}")
# print(f"  Time auto-parsed to datetime: {story.time}")

# # Test 2: Summary with structured output (this is what an LLM will return)
# summary_data = {
#     "headline": "Solo dev launches AI digest tool",
#     "key_points": [
#         "Built with async Python and Pydantic",
#         "Targets Hacker News for daily curation",
#         "Uses Claude for summarization",
#     ],
#     "sentiment": "positive",
#     "story_id": 39512345,
# }
# summary = Summary.model_validate(summary_data)
# print(f"\nSummary: {summary.headline}")
# print(f"  Sentiment: {summary.sentiment}")

# # Test 3: DigestConfig with defaults
# config = DigestConfig()
# print(f"\nDefault config: {config.model_dump()}")

# # Test 4: What happens when validation fails (uncomment to see the error)
# bad = Summary.model_validate({
#     "headline": "Test",
#     "key_points": ["only one"],  # min_length=2 — this will fail
#     "sentiment": "happy",         # not in Literal — this will also fail
#     "story_id": 1,
# })


import time
from functools import wraps

def timed(func):
    """Print how long a function took to run."""
    @wraps(func)  # preserves the original function's name/docstring — important for debugging
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed
def slow_operation():
    time.sleep(0.5)
    return "done"

slow_operation()  # prints: slow_operation took 0.5012s