"""Node 6: PUBLISHER — writes .md files to Obsidian vault."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import aiofiles

from config import VAULT_PATH
from core.state import SAGEState

logger = logging.getLogger("sage.publisher")


def _sanitize_filename(name: str) -> str:
    """Remove characters that are illegal in Windows filenames."""
    # Replace : / \ * ? " < > | with a dash
    sanitized = re.sub(r'[<>:"/\\|?*]', '-', name)
    # Collapse multiple dashes/spaces
    sanitized = re.sub(r'-{2,}', '-', sanitized)
    sanitized = sanitized.strip(' -.')
    # Truncate to safe length (Windows max is 255)
    if len(sanitized) > 180:
        sanitized = sanitized[:180].rstrip(' -')
    return sanitized


def _unit_dir(state: SAGEState) -> Path:
    """Get the unit directory in the Obsidian vault."""
    return (
        VAULT_PATH
        / state["subject"]
        / f"Unit {state['unit_number']} — {state['unit_title']}"
    )


def _build_overview(state: SAGEState) -> str:
    """Build the 00 · Overview.md content."""
    topics_list = "\n".join(f"- {t}" for t in state["all_topics"])
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    nav_links = []
    for i, cluster in enumerate(state["clusters"], start=1):
        title = _sanitize_filename(cluster.topics[0])
        nav_links.append(f"- [[{i:02d} {title}]]")
    nav_links.append(f"- [[{len(state['clusters']) + 1:02d} Quiz & Flashcards]]")
    nav_section = "\n".join(nav_links)

    infographic_embed = ""
    if state["infographic_path"]:
        infographic_embed = "\n## Unit Mind Map\n![[infographic.png]]\n"

    return (
        f"# Unit {state['unit_number']}: {state['unit_title']}\n"
        f"**Subject:** {state['subject']}\n"
        f"**Generated:** {date_str}\n\n"
        f"## Topics Covered\n{topics_list}\n"
        f"{infographic_embed}\n"
        f"## Quick Navigation\n{nav_section}\n"
    )


def _build_cluster_page(cluster) -> str:
    """Build a single cluster .md page."""
    title = cluster.topics[0]

    mermaid_block = ""
    if cluster.mermaid_code:
        mermaid_block = f"\n```mermaid\n{cluster.mermaid_code}\n```\n"

    notes = cluster.notes_content or "_No notes generated._"

    return (
        f"# {title}\n"
        f"**Topic:** {title}\n"
        f"{mermaid_block}\n"
        f"{notes}\n"
    )


def _build_quiz_page(state: SAGEState) -> str:
    """
    Build the consolidated Quiz & Flashcards page.
    Extracts exam prep sections from all cluster notes.
    """
    header = (
        f"# Quiz & Flashcards — Unit {state['unit_number']}\n"
        f"**Subject:** {state['subject']}\n"
        f"**Unit:** {state['unit_title']}\n\n"
        f"---\n\n"
    )

    sections: list[str] = []
    for cluster in state["clusters"]:
        title = cluster.topics[0]
        sections.append(f"## {title}\n")

        # Try to extract exam prep section from notes
        notes = cluster.notes_content or ""
        if "### 🎯 Exam Prep" in notes:
            exam_part = notes.split("### 🎯 Exam Prep")[1]
            # Cut at the next major section if any
            for marker in ["### ", "## ", "---"]:
                if marker in exam_part[10:]:
                    idx = exam_part.index(marker, 10)
                    exam_part = exam_part[:idx]
                    break
            sections.append(exam_part.strip())
        else:
            sections.append("_No exam questions generated for this topic._")

        sections.append("\n---\n")

    return header + "\n".join(sections)


async def publisher_node(state: SAGEState) -> SAGEState:
    """
    Write all generated notes to the Obsidian vault as .md files.

    Reads: state["clusters"][*].notes_content, mermaid_code, infographic_path
    Writes: files to VAULT_PATH/{subject}/Unit {N} — {title}/
    """
    unit_dir = _unit_dir(state)
    unit_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Write Overview page
        overview = _build_overview(state)
        overview_path = unit_dir / "00 Overview.md"
        async with aiofiles.open(overview_path, "w", encoding="utf-8") as f:
            await f.write(overview)
        logger.info(f"Published: {overview_path.name}")

        # 2. Write each cluster page (one per topic)
        for i, cluster in enumerate(state["clusters"], start=1):
            page_content = _build_cluster_page(cluster)
            title = _sanitize_filename(cluster.topics[0])
            filename = f"{i:02d} {title}.md"
            filepath = unit_dir / filename
            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(page_content)
            logger.info(f"Published: {filename}")

        # 3. Write Quiz page
        quiz_content = _build_quiz_page(state)
        quiz_num = len(state["clusters"]) + 1
        quiz_path = unit_dir / f"{quiz_num:02d} Quiz & Flashcards.md"
        async with aiofiles.open(quiz_path, "w", encoding="utf-8") as f:
            await f.write(quiz_content)
        logger.info(f"Published: {quiz_path.name}")

        state["is_complete"] = True
        logger.info(
            f"All files published to {unit_dir} "
            f"({len(state['clusters']) + 2} files)"
        )

    except Exception as e:
        error_msg = f"Publisher error: {e}"
        logger.error(error_msg)
        state["errors"].append(error_msg)

    return state
