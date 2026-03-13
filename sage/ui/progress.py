"""SAGE progress — pipeline status display, spinners, and Rich Live layout."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from ui.theme import COLORS, console
from ui.panels import (
    make_study_header,
    make_pipeline_panel,
    make_activity_panel,
    make_progress_panel,
)


class PipelineTracker:
    """
    Tracks the state of every pipeline node and renders a Live layout.

    Usage:
        async with pipeline_display("NLP", "Unit 1", total_topics=11) as tracker:
            tracker.set_node_running("PLANNER")
            tracker.set_activity("Clustering topics...")
            # ... do work ...
            tracker.set_node_done("PLANNER")
            tracker.advance()  # +1 topic completed
    """

    NODES = ["PLANNER", "RETRIEVER", "EVALUATOR", "WRITER", "STUDIO", "PUBLISHER"]

    def __init__(
        self,
        subject: str,
        unit: str,
        total_topics: int,
    ) -> None:
        self.subject = subject
        self.unit = unit
        self.total_topics = total_topics
        self.completed_topics = 0

        # Track each node status: pending | running | done | failed
        self._node_statuses: dict[str, str] = {n: "pending" for n in self.NODES}

        # Current activity text
        self._activity = "Initializing pipeline..."
        self._cluster_info = ""
        self._depth_info = ""

        # Rich Live instance (set when entering context)
        self._live: Live | None = None

    # ── Node status mutations ────────────────────────────────────

    def set_node_running(self, name: str) -> None:
        """Mark a node as currently running."""
        self._node_statuses[name] = "running"
        self._refresh()

    def set_node_done(self, name: str) -> None:
        """Mark a node as completed."""
        self._node_statuses[name] = "done"
        self._refresh()

    def set_node_failed(self, name: str) -> None:
        """Mark a node as failed."""
        self._node_statuses[name] = "failed"
        self._refresh()

    # ── Activity panel mutations ─────────────────────────────────

    def set_activity(
        self,
        text: str,
        cluster_info: str = "",
        depth_info: str = "",
    ) -> None:
        """Update the right-side activity description."""
        self._activity = text
        if cluster_info:
            self._cluster_info = cluster_info
        if depth_info:
            self._depth_info = depth_info
        self._refresh()

    # ── Progress mutations ───────────────────────────────────────

    def advance(self, count: int = 1) -> None:
        """Increment the completed topics count."""
        self.completed_topics = min(self.completed_topics + count, self.total_topics)
        self._refresh()

    def set_progress(self, completed: int) -> None:
        """Set completed topics to an absolute value."""
        self.completed_topics = min(completed, self.total_topics)
        self._refresh()

    # ── Layout building ──────────────────────────────────────────

    def _build_layout(self) -> Layout:
        """Construct the full Rich Layout."""
        layout = Layout()

        # Top header
        header = make_study_header(self.subject, self.unit)

        # Middle section: pipeline (left) + activity (right)
        middle = Layout()
        pipeline_panel = make_pipeline_panel(self._node_statuses)
        activity_panel = make_activity_panel(
            self._activity,
            self._cluster_info,
            self._depth_info,
        )
        middle.split_row(
            Layout(pipeline_panel, name="pipeline", ratio=1, minimum_size=20),
            Layout(activity_panel, name="activity", ratio=2),
        )

        # Bottom progress
        progress_panel = make_progress_panel(
            self.completed_topics,
            self.total_topics,
        )

        layout.split_column(
            Layout(header, name="header", size=3),
            Layout(middle, name="middle"),
            Layout(progress_panel, name="progress", size=3),
        )

        return layout

    def _refresh(self) -> None:
        """Refresh the Live display if active."""
        if self._live:
            self._live.update(self._build_layout())

    # ── Context manager ──────────────────────────────────────────

    def start(self) -> None:
        """Start the Live display."""
        self._live = Live(
            self._build_layout(),
            console=console,
            refresh_per_second=4,
            screen=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the Live display."""
        if self._live:
            self._live.stop()
            self._live = None


@asynccontextmanager
async def pipeline_display(
    subject: str,
    unit: str,
    total_topics: int,
) -> AsyncGenerator[PipelineTracker, None]:
    """
    Async context manager that provides a PipelineTracker with a live display.

    Usage:
        async with pipeline_display("NLP", "Unit 1", 11) as tracker:
            tracker.set_node_running("PLANNER")
            ...
    """
    tracker = PipelineTracker(subject, unit, total_topics)
    tracker.start()
    try:
        yield tracker
    finally:
        tracker.stop()


def print_dry_run_plan(
    subject: str,
    unit: str,
    clusters: list[dict],
) -> None:
    """
    Print the pipeline plan without executing (for --dry-run flag).

    Args:
        clusters: list of dicts with "cluster_id", "topics", "query"
    """
    from ui.theme import print_banner
    from rich.table import Table
    from rich.panel import Panel

    print_banner(subject=subject, unit=unit)

    console.print()
    console.print(
        f"  [sage.label]DRY RUN[/] — showing plan without executing\n",
    )

    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['secondary']}",
        border_style=COLORS["muted"],
        expand=True,
        padding=(0, 1),
    )
    table.add_column("#", width=3, justify="center")
    table.add_column("Topics", ratio=2)
    table.add_column("Query", ratio=3)

    for c in clusters:
        topics_str = " · ".join(c.get("topics", []))
        table.add_row(
            str(c.get("cluster_id", "?")),
            Text(topics_str, style=COLORS["text"]),
            Text(c.get("query", ""), style=COLORS["muted"]),
        )

    console.print(Panel(
        table,
        title="[sage.label]PLANNED CLUSTERS[/]",
        title_align="left",
        border_style=COLORS["muted"],
    ))
    console.print(
        f"\n  [sage.muted]Run without --dry-run to execute this plan.[/]\n"
    )
