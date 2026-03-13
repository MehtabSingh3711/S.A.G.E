"""Node 5: STUDIO — notebooklm-py generates + downloads infographic."""

from __future__ import annotations

import logging
from pathlib import Path

from config import NOTEBOOKLM_NOTEBOOK_ID, VAULT_PATH
from core.state import SAGEState

logger = logging.getLogger("sage.studio")


from langchain_core.runnables import RunnableConfig

async def studio_node(state: SAGEState, config: RunnableConfig = None) -> SAGEState:
    """
    Generate a unit-level infographic using NotebookLM Studio.

    Reads: state["subject"], state["unit_number"], state["unit_title"]
    Writes: state["infographic_path"]
    """
    tracker = None
    if config and "metadata" in config and "tracker" in config["metadata"]:
        tracker = config["metadata"]["tracker"]

    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        error_msg = "notebooklm-py not installed. Run: pip install notebooklm-py[browser]"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state

    notebook_id = NOTEBOOKLM_NOTEBOOK_ID
    if not notebook_id:
        error_msg = "NOTEBOOKLM_NOTEBOOK_ID not set. Run: sage init"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state

    # Build output path
    unit_dir = (
        VAULT_PATH
        / state["subject"]
        / f"Unit {state['unit_number']} — {state['unit_title']}"
    )
    unit_dir.mkdir(parents=True, exist_ok=True)
    output_path = unit_dir / "infographic.png"

    try:
        if tracker:
            tracker.set_activity("Generating infographic via NotebookLM...")

        async with await NotebookLMClient.from_storage() as client:
            instructions = (
                f"Study cheat sheet for {state['unit_title']}. "
                f"All key concepts, formulas, and comparisons. "
                f"Professional style. University exam prep."
            )

            status = await client.artifacts.generate_infographic(
                notebook_id,
                instructions=instructions,
            )

            task_id = getattr(status, 'task_id', '')
            if not task_id:
                msg = getattr(status, 'error', 'Unknown generation error')
                logger.warning(f"Infographic generation failed API-side: {msg}")
                if tracker:
                    tracker.set_activity("Infographic generation skipped (API constraint)")
                state["infographic_path"] = None
                return state

            if tracker:
                tracker.set_activity("Waiting for studio generator to finish...")

            await client.artifacts.wait_for_completion(
                notebook_id,
                task_id,
            )

            # Download to vault
            await client.artifacts.download_infographic(
                notebook_id,
                str(output_path),
            )

            state["infographic_path"] = str(output_path)
            logger.info(f"Infographic saved to {output_path}")

    except AttributeError:
        # notebooklm-py API may differ — try MCP-based approach
        logger.warning(
            "NotebookLM client API mismatch. "
            "Infographic generation skipped. "
            "Use `sage studio` to generate manually."
        )
        state["infographic_path"] = None

    except Exception as e:
        error_msg = f"Studio error: {e}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        state["infographic_path"] = None

    return state
