"""
SAGE Demo Simulator — produces the exact same Rich UI output
as `python main.py study --unit "Unit 1" --subject "System Design" --syllabus SDunit1.txt`
but finishes in ~30 seconds instead of 30+ minutes.

Usage:
    python simulate.py

Adjust SPEED_FACTOR to make it faster/slower:
    1.0  = ~30 s total  (good for screen recording)
    0.5  = ~15 s total  (fast preview)
    2.0  = ~60 s total  (slower, more dramatic)
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Ensure sage/ is on the path
sys.path.insert(0, str(Path(__file__).parent))

from rich.layout import Layout
from rich.live import Live

from ui.theme import console, print_banner, print_success, COLORS
from ui.panels import (
    make_study_header,
    make_pipeline_panel,
    make_activity_panel,
    make_progress_panel,
)

# ══════════════════════════════════════════════════════════════════
#  Configuration
# ══════════════════════════════════════════════════════════════════

SPEED_FACTOR = 1.0  # Multiply all delays by this factor

SUBJECT = "System Design"
UNIT = "Unit 1"
SYLLABUS_FILE = Path(__file__).parent / "SDunit1.txt"

# Read topics from the actual syllabus file
TOPICS = [
    line.strip()
    for line in SYLLABUS_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

VAULT_PATH = Path(r"C:\Users\mehta\Downloads\SAGE Notes")

# Evaluator follow-up queries for some clusters (simulates depth refinement)
FOLLOWUP_CLUSTERS = {2, 5, 8, 11}


# ══════════════════════════════════════════════════════════════════
#  Flicker-free tracker
#   • Never force-refreshes — lets Rich Live auto-refresh at a
#     steady 4 fps so the panels stay rock-solid.
#   • Uses fixed-size layout slots so the progress bar never
#     jumps vertically.
# ══════════════════════════════════════════════════════════════════

class SmoothTracker:
    """A recording-friendly pipeline tracker that never flickers."""

    NODES = ["PLANNER", "RETRIEVER", "EVALUATOR", "WRITER", "STUDIO", "PUBLISHER"]

    def __init__(self, subject: str, unit: str, total_topics: int) -> None:
        self.subject = subject
        self.unit = unit
        self.total_topics = total_topics
        self.completed_topics = 0
        self._node_statuses: dict[str, str] = {n: "pending" for n in self.NODES}
        self._activity = "Initializing pipeline..."
        self._cluster_info = ""
        self._depth_info = ""
        self._live: Live | None = None

    # ── mutations (NO forced refresh) ────────────────────────────

    def set_node_running(self, name: str) -> None:
        self._node_statuses[name] = "running"

    def set_node_done(self, name: str) -> None:
        self._node_statuses[name] = "done"

    def set_node_failed(self, name: str) -> None:
        self._node_statuses[name] = "failed"

    def set_activity(
        self, text: str, cluster_info: str = "", depth_info: str = ""
    ) -> None:
        self._activity = text
        if cluster_info:
            self._cluster_info = cluster_info
        if depth_info:
            self._depth_info = depth_info

    def advance(self, count: int = 1) -> None:
        self.completed_topics = min(self.completed_topics + count, self.total_topics)

    def set_progress(self, completed: int) -> None:
        self.completed_topics = min(completed, self.total_topics)

    # ── layout (fixed heights) ───────────────────────────────────

    def _build_layout(self) -> Layout:
        layout = Layout()

        header = make_study_header(self.subject, self.unit)

        middle = Layout()
        pipeline_panel = make_pipeline_panel(self._node_statuses)
        activity_panel = make_activity_panel(
            self._activity, self._cluster_info, self._depth_info
        )
        middle.split_row(
            Layout(pipeline_panel, name="pipeline", ratio=1, minimum_size=20),
            Layout(activity_panel, name="activity", ratio=2),
        )

        progress_panel = make_progress_panel(
            self.completed_topics, self.total_topics
        )

        # Fixed sizes prevent the progress bar from jumping
        layout.split_column(
            Layout(header, name="header", size=3),
            Layout(middle, name="middle", size=12),
            Layout(progress_panel, name="progress", size=3),
        )

        return layout

    # ── lifecycle ────────────────────────────────────────────────

    def start(self) -> None:
        self._live = Live(
            self._build_layout(),
            console=console,
            refresh_per_second=4,      # steady 4 fps
            screen=False,
            auto_refresh=True,         # Rich refreshes on its own timer
            transient=False,           # keep final frame on screen
        )
        # Monkey-patch get_renderable so Live always gets the
        # latest layout from our mutable state, without us having
        # to call .update() (which would cause extra redraws).
        self._live.get_renderable = self._build_layout
        self._live.start()

    def stop(self) -> None:
        if self._live:
            self._live.stop()
            self._live = None


# ══════════════════════════════════════════════════════════════════
#  Timing helpers
# ══════════════════════════════════════════════════════════════════

async def wait(seconds: float):
    """Sleep for a scaled duration."""
    await asyncio.sleep(seconds * SPEED_FACTOR)


# ══════════════════════════════════════════════════════════════════
#  Pipeline simulation
# ══════════════════════════════════════════════════════════════════

async def simulate_pipeline():
    """Simulate the full SAGE pipeline with real Rich UI."""

    num_topics = len(TOPICS)
    num_clusters = len(TOPICS)  # 1 cluster per topic (as in real planner)

    tracker = SmoothTracker(SUBJECT, UNIT, num_topics)
    tracker.start()

    try:
        # ── PLANNER ──────────────────────────────────────────────
        tracker.set_node_running("PLANNER")
        tracker.set_activity("Initializing pipeline...")

        await wait(1.0)
        tracker.set_activity("Connecting to Ollama (deepseek-v3.1:671b-cloud)...")
        await wait(1.5)

        tracker.set_activity(
            "Generating queries for each topic...",
            cluster_info=f"{num_topics} topics from SDunit1.txt",
        )
        await wait(2.0)

        # Simulate planner finishing each topic query
        for i, topic in enumerate(TOPICS):
            short = topic[:40] + ("..." if len(topic) > 40 else "")
            tracker.set_activity(
                f"Query generated: {short}",
                cluster_info=f"Cluster {i+1}/{num_clusters}",
            )
            await wait(0.15)

        tracker.set_node_done("PLANNER")
        tracker.set_activity(
            f"Created {num_clusters} clusters",
            cluster_info=f"{num_topics} topics total",
        )
        await wait(0.8)

        # ── RETRIEVER (round 1) ──────────────────────────────────
        tracker.set_node_running("RETRIEVER")
        tracker.set_activity(
            "Connecting to NotebookLM...",
            cluster_info="Launching browser engine",
        )
        await wait(2.5)

        tracker.set_activity(
            "NotebookLM session active",
            cluster_info="Authenticated ✓",
        )
        await wait(1.0)

        for i in range(num_clusters):
            topic = TOPICS[i]
            short_topics = topic[:35] + ("..." if len(topic) > 35 else "")

            tracker.set_activity(
                "Asking NotebookLM...",
                cluster_info=f"[{i+1}/{num_clusters}] {short_topics}",
            )
            await wait(0.6)

            tracker.set_activity(
                "Got answer from NotebookLM",
                cluster_info=f"[{i+1}/{num_clusters}] {short_topics}",
            )
            tracker.set_progress(i + 1)
            await wait(0.3)

        tracker.set_node_done("RETRIEVER")
        tracker.set_activity(
            "Information retrieved from NotebookLM",
            cluster_info=f"Processed all {num_clusters} clusters",
        )
        await wait(0.8)

        # ── EVALUATOR ────────────────────────────────────────────
        tracker.set_node_running("EVALUATOR")
        tracker.set_activity("Evaluating information depth...")
        await wait(1.5)

        followup_count = len(FOLLOWUP_CLUSTERS)
        sufficient = num_clusters - followup_count

        tracker.set_activity(
            f"Evaluated {sufficient}/{num_clusters} as deep enough",
            depth_info=f"{followup_count} clusters need follow-up queries",
        )
        await wait(1.0)

        # Simulate follow-up round — evaluator sends back to retriever
        tracker.set_node_done("EVALUATOR")
        tracker.set_activity(
            "Follow-up queries needed",
            cluster_info=f"{followup_count} clusters flagged for deeper retrieval",
            depth_info="Routing back to RETRIEVER...",
        )
        await wait(0.8)

        # ── RETRIEVER (round 2 — follow-ups) ─────────────────────
        tracker.set_node_running("RETRIEVER")
        tracker.set_activity(
            "Processing follow-up queries...",
            cluster_info="Depth refinement round",
        )
        await wait(1.0)

        for idx, cluster_num in enumerate(sorted(FOLLOWUP_CLUSTERS)):
            topic = TOPICS[cluster_num - 1]
            short = topic[:35] + ("..." if len(topic) > 35 else "")

            tracker.set_activity(
                "Asking follow-up query...",
                cluster_info=f"[{idx+1}/{followup_count}] {short}",
                depth_info="Query depth: 2/2",
            )
            await wait(0.5)

            tracker.set_activity(
                "Got follow-up answer",
                cluster_info=f"[{idx+1}/{followup_count}] {short}",
                depth_info="Query depth: 2/2",
            )
            await wait(0.3)

        tracker.set_node_done("RETRIEVER")
        await wait(0.5)

        # ── EVALUATOR (round 2) ──────────────────────────────────
        tracker.set_node_running("EVALUATOR")
        tracker.set_activity(
            f"Re-evaluating {followup_count} follow-up answers...",
            depth_info="Checking sufficiency...",
        )
        await wait(1.0)

        tracker.set_activity(
            f"Evaluated {num_clusters}/{num_clusters} as deep enough",
            depth_info="All clusters sufficient ✓",
        )
        tracker.set_node_done("EVALUATOR")
        await wait(0.8)

        # ── WRITER ───────────────────────────────────────────────
        tracker.set_node_running("WRITER")
        tracker.set_activity("Generating Obsidian-compatible markdown notes...")
        await wait(1.5)

        for i in range(num_clusters):
            topic = TOPICS[i]
            short = topic[:35] + ("..." if len(topic) > 35 else "")
            tracker.set_activity(
                f"Writing notes: {short}",
                cluster_info=f"Cluster {i+1}/{num_clusters}",
            )
            await wait(0.4)

        tracker.set_node_done("WRITER")
        tracker.set_activity(
            f"Written notes for {num_clusters}/{num_clusters} clusters",
        )
        await wait(0.8)

        # ── STUDIO ───────────────────────────────────────────────
        tracker.set_node_running("STUDIO")
        tracker.set_activity(
            "Generating Mermaid infographic...",
            cluster_info="Creating visual overview of all topics",
        )
        await wait(2.0)

        infographic_path = VAULT_PATH / SUBJECT / f"Unit 1 — {UNIT}" / "infographic.md"
        tracker.set_activity(
            "Infographic generated",
            cluster_info=f"Saved to: {infographic_path}",
        )
        tracker.set_node_done("STUDIO")
        await wait(0.8)

        # ── PUBLISHER ────────────────────────────────────────────
        tracker.set_node_running("PUBLISHER")
        tracker.set_activity("Publishing notes to Obsidian vault...")
        await wait(1.0)

        tracker.set_activity(
            "Creating folder structure...",
            cluster_info=str(VAULT_PATH / SUBJECT / "Unit 1"),
        )
        await wait(0.5)

        for i in range(num_clusters):
            topic = TOPICS[i]
            short = topic[:35] + ("..." if len(topic) > 35 else "")
            tracker.set_activity(
                f"Saving: {short}.md",
                cluster_info=f"File {i+1}/{num_clusters}",
            )
            await wait(0.15)

        tracker.set_activity(
            "Writing MOC (Map of Content)...",
            cluster_info="Linking all notes together",
        )
        await wait(0.8)

        tracker.set_activity("All notes published to vault.")
        tracker.set_node_done("PUBLISHER")
        await wait(0.5)

        # Mark all progress complete
        tracker.set_progress(num_topics)
        await wait(1.0)

    finally:
        tracker.stop()

    # ── Final success message ────────────────────────────────────
    console.print()
    print_success(f"Notes published to {VAULT_PATH / SUBJECT / 'Unit 1 — Unit 1'}")
    console.print()


# ══════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════

def main():
    # Print the banner (same as real `sage study`)
    print_banner(subject=SUBJECT, unit=UNIT)

    # Show topics loaded message
    console.print(f"  [sage.muted]→ {len(TOPICS)} topics loaded from SDunit1.txt[/]")
    console.print()

    # Small pause before pipeline starts (looks natural in recording)
    time.sleep(0.5 * SPEED_FACTOR)

    # Run the simulated pipeline
    asyncio.run(simulate_pipeline())


if __name__ == "__main__":
    main()
