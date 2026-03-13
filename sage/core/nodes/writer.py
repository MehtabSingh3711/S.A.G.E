"""Node 4: WRITER — GLM-5 writes structured notes + Mermaid diagrams."""

from __future__ import annotations

import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from core.state import SAGEState
from prompts.writer_prompt import WRITER_SYSTEM_PROMPT, MERMAID_INSTRUCTION

logger = logging.getLogger("sage.writer")

MERMAID_START = "===MERMAID_START==="
MERMAID_END = "===MERMAID_END==="


def _build_grounded_content(cluster) -> str:
    """Combine raw answer and follow-up answer into one grounded block."""
    parts: list[str] = []
    if cluster.raw_answer:
        parts.append(cluster.raw_answer)
    if cluster.follow_up_answer:
        parts.append(f"\n\n--- Additional Detail ---\n\n{cluster.follow_up_answer}")
    return "\n".join(parts) if parts else "No content retrieved."


def _extract_notes_and_mermaid(content: str) -> tuple[str, str]:
    """
    Split LLM response into (notes_markdown, mermaid_code).
    Uses the ===MERMAID_START=== / ===MERMAID_END=== markers.
    If markers are missing, the entire response is treated as notes.
    """
    notes = content.strip()
    mermaid = ""

    if MERMAID_START in content:
        parts = content.split(MERMAID_START, 1)
        notes = parts[0].strip()

        mermaid_block = parts[1] if len(parts) > 1 else ""
        if MERMAID_END in mermaid_block:
            mermaid = mermaid_block.split(MERMAID_END, 1)[0].strip()
        else:
            # No end marker — take everything after start marker
            mermaid = mermaid_block.strip()

    # Clean up: remove any ```mermaid wrapping the LLM might add anyway
    if mermaid.startswith("```mermaid"):
        mermaid = mermaid[len("```mermaid"):].strip()
    if mermaid.startswith("```"):
        mermaid = mermaid[3:].strip()
    if mermaid.endswith("```"):
        mermaid = mermaid[:-3].strip()

    return notes, mermaid


async def writer_node(state: SAGEState, config: RunnableConfig = None) -> SAGEState:
    """
    Use GLM-5 to transform retrieved content into beautiful structured notes
    and Mermaid diagrams.

    Reads: state["clusters"][*].raw_answer, follow_up_answer, topics
    Writes: state["clusters"][*].notes_content, state["clusters"][*].mermaid_code
    """
    tracker = None
    if config and "metadata" in config and "tracker" in config["metadata"]:
        tracker = config["metadata"]["tracker"]

    # NO format="json" — we want raw markdown output
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
    )

    for i, cluster in enumerate(state["clusters"]):
        state["current_cluster_idx"] = i

        topics_str = ", ".join(cluster.topics)
        short_topics = topics_str[:35] + ("..." if len(topics_str) > 35 else "")

        if tracker:
            tracker.set_activity(
                "Writing structured notes...",
                cluster_info=f"[{i+1}/{len(state['clusters'])}] {short_topics}",
            )

        if cluster.notes_content:
            continue  # already written (resume support)

        grounded = _build_grounded_content(cluster)

        system_prompt = WRITER_SYSTEM_PROMPT.format(
            topics=topics_str,
            subject=state["subject"],
        )
        full_system = system_prompt + "\n\n" + MERMAID_INSTRUCTION

        user_message = (
            f"Here is the grounded content extracted from textbooks:\n\n"
            f"{grounded}\n\n"
            f"Write the study notes and Mermaid diagram for these topics: {topics_str}"
        )

        try:
            if tracker:
                tracker.set_activity(
                    f"Generating notes with GLM-5...",
                    cluster_info=f"[{i+1}/{len(state['clusters'])}] {short_topics}",
                )

            response = await llm.ainvoke([
                SystemMessage(content=full_system),
                HumanMessage(content=user_message),
            ])

            content = response.content.strip()

            # Split into notes + mermaid using markers
            notes, mermaid = _extract_notes_and_mermaid(content)

            cluster.notes_content = notes
            cluster.mermaid_code = mermaid

            # If notes is empty somehow, use the full response
            if not cluster.notes_content:
                logger.warning(
                    f"Cluster {cluster.cluster_id}: notes extraction returned empty, "
                    f"using full response."
                )
                cluster.notes_content = content

            logger.info(
                f"Cluster {cluster.cluster_id}: wrote "
                f"{len(cluster.notes_content)} chars of notes, "
                f"{len(cluster.mermaid_code)} chars of mermaid"
            )

        except Exception as e:
            error_msg = f"Writer error for cluster {cluster.cluster_id}: {e}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            cluster.notes_content = (
                f"## {topics_str}\n\n"
                f"_Note generation failed. Raw content below:_\n\n"
                f"{grounded}"
            )
            cluster.mermaid_code = ""

    return state
