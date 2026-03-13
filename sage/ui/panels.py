"""SAGE panels — Rich panel/layout components for pipeline and chat displays."""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich import box

from ui.theme import COLORS, console


# ── Pipeline Node Status Icons ───────────────────────────────────
STATUS_ICONS = {
    "done": ("✓", "sage.done"),
    "running": ("⟳", "sage.running"),
    "pending": ("○", "sage.pending"),
    "failed": ("✗", "sage.failed"),
}

NODE_NAMES = [
    "PLANNER",
    "RETRIEVER",
    "EVALUATOR",
    "WRITER",
    "STUDIO",
    "PUBLISHER",
]


def make_pipeline_panel(node_statuses: dict[str, str]) -> Panel:
    """
    Build the left pipeline status panel.

    Args:
        node_statuses: dict mapping node name → status string
                       e.g. {"PLANNER": "done", "RETRIEVER": "running", ...}
    """
    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("status", width=3)
    table.add_column("name")

    for name in NODE_NAMES:
        status = node_statuses.get(name, "pending")
        icon, style = STATUS_ICONS.get(status, STATUS_ICONS["pending"])
        table.add_row(
            Text(f" {icon}", style=style),
            Text(f" {name}", style=style),
        )

    return Panel(
        table,
        title="[sage.label]PIPELINE[/]",
        title_align="left",
        border_style=COLORS["muted"],
        padding=(1, 1),
    )


def make_activity_panel(
    activity_text: str,
    cluster_info: str = "",
    depth_info: str = "",
) -> Panel:
    """
    Build the right-side activity panel showing current work.

    Args:
        activity_text: Main activity description (e.g. "Retrieving: Parsing...")
        cluster_info: e.g. "Cluster 2 of 3"
        depth_info: e.g. "Query depth: 1/2"
    """
    content = Text()
    content.append(f"  {activity_text}\n\n", style=COLORS["text"])
    if cluster_info:
        content.append(f"  {cluster_info}\n", style=COLORS["muted"])
    if depth_info:
        content.append(f"  {depth_info}", style=COLORS["muted"])

    return Panel(
        content,
        title="[sage.label]CURRENT ACTIVITY[/]",
        title_align="left",
        border_style=COLORS["muted"],
        padding=(1, 1),
    )


def make_progress_panel(
    completed: int,
    total: int,
    label: str = "topics",
) -> Panel:
    """Build the bottom progress bar panel."""
    if total == 0:
        pct = 0.0
    else:
        pct = completed / total

    bar_width = 40
    filled = int(bar_width * pct)
    empty = bar_width - filled

    bar = Text()
    bar.append("  ")
    bar.append("█" * filled, style=COLORS["primary"])
    bar.append("░" * empty, style=COLORS["muted"])
    bar.append(f"  {completed}/{total} {label}", style=COLORS["text"])

    return Panel(
        bar,
        title="[sage.label]PROGRESS[/]",
        title_align="left",
        border_style=COLORS["muted"],
        padding=(0, 1),
    )


def make_study_header(subject: str, unit: str) -> Panel:
    """Build the top header bar for sage study."""
    header = Text()
    header.append("  SAGE", style=f"bold {COLORS['primary']}")
    header.append("  ·  ", style=COLORS["muted"])
    header.append(subject, style=f"bold {COLORS['text']}")
    header.append("  ·  ", style=COLORS["muted"])
    header.append(unit, style=COLORS["text"])

    return Panel(
        header,
        border_style=COLORS["muted"],
        padding=(0, 1),
    )


def make_chat_header(subject: str | None = None) -> Panel:
    """Build the header for sage chat mode."""
    header = Text()
    header.append("  SAGE CHAT", style=f"bold {COLORS['primary']}")
    if subject:
        header.append("  ·  ", style=COLORS["muted"])
        header.append(subject, style=f"bold {COLORS['text']}")

    return Panel(
        header,
        border_style=COLORS["muted"],
        padding=(0, 1),
    )


def make_chat_message(role: str, content: str, sources: list[str] | None = None) -> Text:
    """Format a single chat message."""
    msg = Text()
    if role == "user":
        msg.append("  You: ", style=f"bold {COLORS['accent']}")
        msg.append(content, style=COLORS["text"])
    else:
        msg.append("  SAGE: ", style=f"bold {COLORS['primary']}")
        msg.append(content, style=COLORS["text"])
        if sources:
            msg.append("\n        Sources: ", style=COLORS["muted"])
            for src in sources:
                msg.append(f"[{src}] ", style=f"italic {COLORS['secondary']}")
    return msg


def make_status_table(
    notebook_info: dict,
    vault_info: dict,
) -> Panel:
    """Build the status display table for `sage status`."""
    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
        expand=True,
    )
    table.add_column("key", style=COLORS["secondary"], min_width=20)
    table.add_column("value", style=COLORS["text"])

    # Notebook section
    table.add_row("📓 Notebook ID", notebook_info.get("id", "Not set"))
    table.add_row("   Title", notebook_info.get("title", "Unknown"))
    table.add_row("   Sources", str(notebook_info.get("source_count", 0)))
    table.add_row("", "")

    # Vault section
    table.add_row("📁 Vault Path", vault_info.get("path", "Not set"))
    table.add_row("   Subjects", str(vault_info.get("subject_count", 0)))
    table.add_row("   Total Notes", str(vault_info.get("note_count", 0)))
    table.add_row("   Size", vault_info.get("size", "0 KB"))

    return Panel(
        table,
        title="[sage.label]SAGE STATUS[/]",
        title_align="left",
        border_style=COLORS["muted"],
        padding=(1, 1),
    )


def make_init_step_panel(step: int, total: int, title: str, description: str) -> Panel:
    """Build a panel for each init wizard step."""
    header = Text()
    header.append(f"  Step {step}/{total}: ", style=f"bold {COLORS['primary']}")
    header.append(title, style=f"bold {COLORS['text']}")
    header.append(f"\n  {description}", style=COLORS["muted"])

    return Panel(
        header,
        border_style=COLORS["secondary"],
        padding=(0, 1),
    )
