"""SAGE CLI — main entry point with Typer commands."""

from __future__ import annotations

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Prompt, Confirm

# Ensure sage/ is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    VAULT_PATH,
    NOTEBOOKLM_NOTEBOOK_ID,
)
from ui.theme import console, print_banner, print_error, print_success, print_warning, print_info, COLORS
from ui.panels import make_status_table, make_init_step_panel

app = typer.Typer(
    name="sage",
    help="SAGE — Study · Ask · Generate · Explain",
    add_completion=False,
    no_args_is_help=True,
)


# ═══════════════════════════════════════════════════════════════════
#  sage study
# ═══════════════════════════════════════════════════════════════════

@app.command()
def study(
    unit: str = typer.Option(..., "--unit", "-u", help="Unit name, e.g. 'Unit 1'"),
    subject: str = typer.Option(..., "--subject", "-s", help="Subject name, e.g. 'NLP'"),
    resume: bool = typer.Option(False, "--resume", help="Resume from last checkpoint"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    topics: Optional[str] = typer.Option(None, "--topics", "-t", help="Comma-separated topic list"),
    syllabus: Optional[Path] = typer.Option(None, "--syllabus", help="Path to .txt or .pdf syllabus file"),
    unit_number: int = typer.Option(1, "--unit-number", "-n", help="Unit number for PDF parsing"),
):
    """Run the full SAGE study pipeline — plan, retrieve, write, publish."""
    print_banner(subject=subject, unit=unit)

    # Validate prerequisites
    if not _check_prerequisites():
        raise typer.Exit(1)

    # Parse unit number from unit string
    unit_number = _parse_unit_number(unit)
    unit_title = unit.replace(f"Unit {unit_number}", "").strip(" —-·")
    if not unit_title:
        unit_title = unit

    # Ask for topics
    # Resolve topics from flags or interactive input
    final_topics: list[str] = []

    if topics:
        # --topics "Topic 1, Topic 2, Topic 3"
        final_topics = [t.strip() for t in topics.split(",") if t.strip()]
        console.print(f"  [sage.muted]→ {len(final_topics)} topics loaded from --topics[/]")

    elif syllabus:
        if syllabus.suffix == ".txt":
            final_topics = [
                line.strip()
                for line in syllabus.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            console.print(f"  [sage.muted]→ {len(final_topics)} topics loaded from {syllabus.name}[/]")
        elif syllabus.suffix == ".pdf":
            print_warning("PDF syllabus parsing not yet implemented. Use --topics or a .txt file.")
            raise typer.Exit(1)
        else:
            print_error(f"Unsupported syllabus format: {syllabus.suffix}. Use .txt")
            raise typer.Exit(1)

    else:
        # Fallback — interactive input
        console.print()
        console.print(f"  [sage.label]Enter topics[/] [sage.muted](comma-separated):[/]")
        topics_input = console.input(f"  [{COLORS['accent']}]› [/]").strip()
        if not topics_input:
            print_error("No topics provided. Exiting.")
            raise typer.Exit(1)
        final_topics = [t.strip() for t in topics_input.split(",") if t.strip()]
        console.print(f"  [sage.muted]→ {len(final_topics)} topics loaded[/]")

    topics = final_topics  # reassign so rest of function uses it
    if dry_run:
        _run_dry_run(subject, unit, unit_number, unit_title, topics)
        return

    # Run the full pipeline
    asyncio.run(_run_study(subject, unit, unit_number, unit_title, topics))


async def _run_study(
    subject: str,
    unit: str,
    unit_number: int,
    unit_title: str,
    topics: list[str],
):
    """Execute the full study pipeline with live UI."""
    from ui.progress import pipeline_display
    from core.pipeline import run_pipeline

    async with pipeline_display(subject, unit, len(topics)) as tracker:
        final_state = await run_pipeline(
            subject=subject,
            unit_number=unit_number,
            unit_title=unit_title,
            topics=topics,
            tracker=tracker,
        )

    console.print()
    if final_state.get("is_complete"):
        print_success(
            f"Notes published to {VAULT_PATH / subject / f'Unit {unit_number} — {unit_title}'}"
        )
    else:
        print_warning("Pipeline completed with errors:")
        for err in final_state.get("errors", []):
            console.print(f"  [sage.error]• {err}[/]")
    console.print()


def _run_dry_run(
    subject: str,
    unit: str,
    unit_number: int,
    unit_title: str,
    topics: list[str],
):
    """Run planner only and display the plan."""
    from core.state import SAGEState
    from core.nodes.planner import planner_node
    from ui.progress import print_dry_run_plan

    console.print()
    with console.status(
        f"  [sage.primary]Planning with GLM-5...[/]",
        spinner="dots",
    ):
        state = {
            "subject": subject,
            "unit_number": unit_number,
            "unit_title": unit_title,
            "all_topics": topics,
            "clusters": [],
            "infographic_path": None,
            "current_cluster_idx": 0,
            "errors": [],
            "is_complete": False,
        }
        state = asyncio.run(planner_node(state))

    clusters = [
        {
            "cluster_id": c.cluster_id,
            "topics": c.topics,
            "query": c.query,
        }
        for c in state["clusters"]
    ]
    print_dry_run_plan(subject, unit, clusters)


# ═══════════════════════════════════════════════════════════════════
#  sage chat
# ═══════════════════════════════════════════════════════════════════

@app.command()
def chat(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="One-shot query"),
):
    """Chat with your notebook — ask anything about your sources."""
    print_banner()

    if not _check_prerequisites():
        raise typer.Exit(1)

    from core.chat import chat_loop, one_shot_query

    if query:
        asyncio.run(one_shot_query(query))
    else:
        asyncio.run(chat_loop())


# ═══════════════════════════════════════════════════════════════════
#  sage status
# ═══════════════════════════════════════════════════════════════════

@app.command()
def status():
    """Show current notebook + vault stats."""
    print_banner()
    console.print()

    # Gather notebook info
    notebook_info = {
        "id": NOTEBOOKLM_NOTEBOOK_ID or "Not configured",
        "title": "Unknown",
        "source_count": 0,
    }

    # Gather vault info
    vault_path = VAULT_PATH
    vault_info = {
        "path": str(vault_path),
        "subject_count": 0,
        "note_count": 0,
        "size": "0 KB",
    }

    if vault_path.exists():
        subjects = [
            d for d in vault_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        vault_info["subject_count"] = len(subjects)

        note_count = 0
        total_size = 0
        for md_file in vault_path.rglob("*.md"):
            note_count += 1
            total_size += md_file.stat().st_size

        vault_info["note_count"] = note_count

        if total_size < 1024:
            vault_info["size"] = f"{total_size} B"
        elif total_size < 1048576:
            vault_info["size"] = f"{total_size / 1024:.1f} KB"
        else:
            vault_info["size"] = f"{total_size / 1048576:.1f} MB"

    console.print(make_status_table(notebook_info, vault_info))
    console.print()


# ═══════════════════════════════════════════════════════════════════
#  sage init
# ═══════════════════════════════════════════════════════════════════

@app.command()
def init():
    """First-time setup wizard — configure Ollama, NotebookLM, and vault."""
    print_banner()
    console.print()
    console.print(
        f"  [sage.label]Welcome to SAGE Setup[/]  "
        f"[sage.muted]Let's get everything configured.[/]"
    )
    console.print()

    env_values: dict[str, str] = {}

    # ── Step 1: Ollama ───────────────────────────────────────────
    console.print(make_init_step_panel(
        1, 4, "Ollama & GLM-5",
        "Check that Ollama is running and deepseek-v3.1:671b-cloud is available",
    ))
    console.print()

    ollama_ok = _check_ollama()
    if not ollama_ok:
        console.print()
        print_error(
            "Ollama is not running. Start it with: ollama serve\n"
            "  Then pull the model: ollama pull deepseek-v3.1:671b-cloud"
        )
        if not Confirm.ask(
            f"  [{COLORS['muted']}]Continue anyway?[/]",
            default=False,
            console=console,
        ):
            raise typer.Exit(1)

    base_url = Prompt.ask(
        f"  [{COLORS['text']}]Ollama URL[/]",
        default="http://localhost:11434",
        console=console,
    )
    env_values["OLLAMA_BASE_URL"] = base_url
    console.print()

    # ── Step 2: NotebookLM ───────────────────────────────────────
    console.print(make_init_step_panel(
        2, 4, "NotebookLM Authentication",
        "Connect to NotebookLM for grounded retrieval",
    ))
    console.print()

    print_info("If not authenticated, run: notebooklm login")
    console.print()

    notebook_id = Prompt.ask(
        f"  [{COLORS['text']}]Notebook ID[/]",
        default=NOTEBOOKLM_NOTEBOOK_ID or "",
        console=console,
    )
    env_values["NOTEBOOKLM_NOTEBOOK_ID"] = notebook_id
    console.print()

    # ── Step 3: Obsidian Vault ───────────────────────────────────
    console.print(make_init_step_panel(
        3, 4, "Obsidian Vault",
        "Set the path where SAGE will write your study notes",
    ))
    console.print()

    vault_input = Prompt.ask(
        f"  [{COLORS['text']}]Vault path[/]",
        default=str(VAULT_PATH),
        console=console,
    )
    vault_path = Path(vault_input)

    try:
        vault_path.mkdir(parents=True, exist_ok=True)
        test_file = vault_path / ".sage_test"
        test_file.write_text("sage")
        test_file.unlink()
        print_success(f"Vault path verified: {vault_path}")
    except Exception as e:
        print_error(f"Cannot write to vault path: {e}")
        if not Confirm.ask(
            f"  [{COLORS['muted']}]Continue anyway?[/]",
            default=False,
            console=console,
        ):
            raise typer.Exit(1)

    env_values["OBSIDIAN_VAULT_PATH"] = str(vault_path)
    console.print()

    # ── Step 4: Save .env ────────────────────────────────────────
    console.print(make_init_step_panel(
        4, 4, "Save Configuration",
        "Write settings to .env file",
    ))
    console.print()

    # Show summary
    for key, value in env_values.items():
        display_val = value if len(value) < 50 else value[:47] + "..."
        console.print(f"  [sage.secondary]{key}[/] = [sage.text]{display_val}[/]")
    console.print()

    if Confirm.ask(
        f"  [{COLORS['text']}]Save to .env?[/]",
        default=True,
        console=console,
    ):
        env_path = Path(__file__).parent / ".env"
        lines: list[str] = []
        for key, value in env_values.items():
            lines.append(f"{key}={value}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print_success(f"Configuration saved to {env_path}")
    else:
        print_warning("Configuration not saved.")

    console.print()

    # ── Health check ─────────────────────────────────────────────
    console.print(f"  [sage.label]Running health check...[/]")
    console.print()

    checks = {
        "Ollama": _check_ollama(),
        "Vault writable": vault_path.exists() and os.access(str(vault_path), os.W_OK),
        "Notebook ID set": bool(notebook_id),
    }

    for name, passed in checks.items():
        icon = "✓" if passed else "✗"
        style = "sage.accent" if passed else "sage.error"
        console.print(f"  [{style}]{icon}[/]  {name}")

    console.print()
    all_ok = all(checks.values())
    if all_ok:
        print_success("All checks passed! Run: sage study --unit 'Unit 1' --subject 'NLP'")
    else:
        print_warning("Some checks failed. Fix the issues above and run: sage init")
    console.print()


# ═══════════════════════════════════════════════════════════════════
#  Helper functions
# ═══════════════════════════════════════════════════════════════════

def _check_ollama() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        import urllib.request
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_prerequisites() -> bool:
    """Validate all prerequisites before running a command."""
    errors: list[str] = []

    # Check Ollama
    if not _check_ollama():
        print_error("Ollama is not running. Start with: ollama serve")
        errors.append("ollama")

    # Check vault path
    if not VAULT_PATH.parent.exists():
        print_error(f"Vault path not found: {VAULT_PATH}. Run: sage init")
        errors.append("vault")

    # Check notebook ID
    if not NOTEBOOKLM_NOTEBOOK_ID:
        print_error("NOTEBOOKLM_NOTEBOOK_ID not set. Run: sage init")
        errors.append("notebook")

    return len(errors) == 0


def _parse_unit_number(unit_str: str) -> int:
    """Extract unit number from a string like 'Unit 1' or 'Unit 3 — Parsing'."""
    import re
    match = re.search(r"\d+", unit_str)
    if match:
        return int(match.group())
    return 1


# ═══════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app()
