"""Day 4 exercise: read sample HN stories, filter + categorize them,
write a summary report. Uses comprehensions, context managers,
a custom decorator, and match/case.
"""

import json
import time
from functools import wraps
from pathlib import Path


def timed(func):
    """Decorator: prints how long the wrapped function took."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [timing] {func.__name__}: {elapsed * 1000:.2f}ms")
        return result
    return wrapper


def categorize_story(title: str) -> str:
    """Pattern-match a category from keywords in the title."""
    title_lower = title.lower()
    match title_lower:
        case t if "gpt" in t or "llm" in t or "ai" in t or "langchain" in t or "langgraph" in t:
            return "ai"
        case t if "react" in t or "tailwind" in t or "solid" in t:
            return "frontend"
        case t if "postgres" in t or "database" in t or "rust" in t:
            return "infra"
        case _:
            return "other"


@timed
def load_stories(path: Path) -> list[dict]:
    """Read sample stories from disk using a context manager."""
    with open(path) as f:
        return json.load(f)


@timed
def analyze(stories: list[dict], min_score: int = 50) -> dict:
    """Filter, categorize, and aggregate."""
    # List comprehension: filter by score, enrich with category
    enriched = [
        {**story, "category": categorize_story(story["title"])}
        for story in stories
        if story["score"] >= min_score
    ]
    
    # print(f"enriched: {enriched}")

    # Set comprehension: unique categories present
    categories_present = {s["category"] for s in enriched}

    # Dict comprehension: count stories per category
    counts_by_category = {
        cat: sum(1 for s in enriched if s["category"] == cat)
        for cat in categories_present
    }

    # Generator expression in sum() — no intermediate list
    avg_score = sum(s["score"] for s in enriched) / len(enriched) if enriched else 0

    return {
        "total_above_threshold": len(enriched),
        "categories": counts_by_category,
        "avg_score": round(avg_score, 1),
        "stories": enriched,
    }


def test_Comprehensiosn(list):
    list = [1, 2, 3, 4, 5];
    # List comprehension: filter even numbers
    odd_Squars = sum(n**2 for n in list if n % 2 == 1)
    return odd_Squars



def main():
    here = Path(__file__).parent
    stories = load_stories(here / "sample_stories.json")
    report = analyze(stories, min_score=50)
    print(test_Comprehensiosn(list));
    # Pretty-print summary
    print(f"\nLoaded {len(stories)} stories total.")
    print(f"After filtering (score >= 50): {report['total_above_threshold']} stories")
    print(f"Average score: {report['avg_score']}")
    print(f"By category: {report['categories']}")

    # Write the enriched output (context manager again)
    out_path = here / "filtered_stories.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nWrote enriched report to {out_path.name}")


if __name__ == "__main__":
    main()