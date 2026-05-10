"""Render summarized stories as a markdown digest."""

from datetime import datetime
from pathlib import Path

from daily_ai_digest.models import HackerNewsStory, Summary


def render_digest(
    pairs: list[tuple[HackerNewsStory, Summary]],
    out_path: Path,
) -> None:
    """Write `pairs` as a markdown digest to `out_path`.

    Each pair is (original story, LLM-generated summary). Order is preserved.
    """
    today = datetime.now().strftime("%B %d, %Y")
    lines: list[str] = [
        f"# Daily AI Digest — {today}",
        "",
        f"_{len(pairs)} stories from Hacker News, summarized by Claude._",
        "",
        "---",
        "",
    ]

    for i, (story, summary) in enumerate(pairs, start=1):
        # Header: numbered headline
        lines.append(f"## {i}. {summary.headline}")
        lines.append("")

        # Metadata line
        meta = f"**{story.score} points** · by {story.author} · sentiment: _{summary.sentiment}_"
        lines.append(meta)
        lines.append("")

        # Bullet points (the LLM-generated key points)
        for point in summary.key_points:
            lines.append(f"- {point}")
        lines.append("")

        # Link back to the original
        if story.url:
            lines.append(f"[Original: {story.title}]({story.url})")
        else:
            lines.append(f"_Original (text post): {story.title}_")

        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")