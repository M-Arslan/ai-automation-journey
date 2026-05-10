"""Daily AI Digest CLI.

Run with:
    uv run digest run --count 10 --out digest.md
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from daily_ai_digest.fetch_async import fetch_top_stories
from daily_ai_digest.models import HackerNewsStory, Summary
from daily_ai_digest.render import render_digest
from daily_ai_digest.summarize import summarize_structured_async

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def run(
    count: int = typer.Option(10, "--count", "-c", help="Number of top stories."),
    out: Path = typer.Option(Path("digest.md"), "--out", "-o", help="Output file."),
    concurrency: int = typer.Option(5, help="Max concurrent LLM calls."),
) -> None:
    """Fetch HN top stories, summarize each, write a markdown digest."""
    asyncio.run(_run_async(count=count, out=out, concurrency=concurrency))


async def _run_async(count: int, out: Path, concurrency: int) -> None:
    console.rule("[bold]Daily AI Digest[/bold]")

    # --- 1. Fetch stories ---
    with console.status("[cyan]Fetching top stories from Hacker News..."):
        stories = await fetch_top_stories(limit=count)
    console.print(f"  Fetched [green]{len(stories)}[/green] stories")

    # --- 2. Summarize in parallel, bounded by Semaphore ---
    sem = asyncio.Semaphore(concurrency)

    async def summarize_one(
        story: HackerNewsStory,
        progress: Progress,
        task_id: int,
    ) -> Summary | Exception:
        async with sem:
            try:
                text = (
                    f"Title: {story.title}\n"
                    f"URL: {story.url}\n"
                    f"Score: {story.score}"
                )
                result = await summarize_structured_async(text, story_id=story.id)
                progress.advance(task_id)
                return result
            except Exception as e:
                progress.advance(task_id)
                return e

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(
            f"Summarizing {len(stories)} stories...", total=len(stories)
        )
        results = await asyncio.gather(
            *[summarize_one(s, progress, task_id) for s in stories]
        )

    # --- 3. Filter out failures and pair successful summaries with stories ---
    pairs: list[tuple[HackerNewsStory, Summary]] = []
    for story, result in zip(stories, results):
        if isinstance(result, Exception):
            console.print(
                f"  [yellow]Skipped[/yellow] '{story.title}': {result}"
            )
        else:
            pairs.append((story, result))

    # --- 4. Render ---
    render_digest(pairs, out)
    console.print(f"\n  Wrote digest with [green]{len(pairs)}[/green] stories to [bold]{out}[/bold]")
    console.rule()


if __name__ == "__main__":
    app()