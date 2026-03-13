from __future__ import annotations

import logging
import asyncio

from langchain_core.runnables import RunnableConfig

from core.state import SAGEState
from config import NOTEBOOKLM_NOTEBOOK_ID

logger = logging.getLogger("sage.retriever")


async def retriever_node(state: SAGEState, config: RunnableConfig = None) -> SAGEState:
    """
    Connect to NotebookLM and retrieve context for all clusters.

    Reads: state["clusters"][*].topics, query, follow_up_query
    Writes: state["clusters"][*].raw_answer, follow_up_answer
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

    # Auth: relies on notebooklm-py's own storage_state.json
    # Run `notebooklm login` to authenticate (one-time browser login)

    try:
        client_init = await NotebookLMClient.from_storage()
    except Exception as e:
        error_msg = "NotebookLM Auth Error. Please run 'notebooklm login' in your terminal."
        logger.error(f"{error_msg} Details: {e}")
        state["errors"].append(error_msg)
        if tracker:
            tracker.set_activity("NotebookLM Auth Error", cluster_info="Please run 'notebooklm login'")
        raise ValueError(error_msg)

    try:
        async with client_init as client:
            clusters = state.get("clusters", [])
            for i, cluster in enumerate(clusters):
                state["current_cluster_idx"] = i  # Update progress for UI

                topics_str = ", ".join(cluster.topics)
                short_topics = topics_str[:35] + ("..." if len(topics_str) > 35 else "")

                # Primary query
                if not cluster.raw_answer:
                    if tracker:
                        tracker.set_activity(
                            "Asking NotebookLM...",
                            cluster_info=f"[{i+1}/{len(clusters)}] {short_topics}",
                        )
                    logger.info(f"Querying cluster {i+1}/{len(clusters)}: {topics_str}")
                    
                    try:
                        # Depending on notebooklm-py version, checking methods:
                        # Assuming client.chat.send_message
                        full_query = f"Give everything you find about {cluster.query} from the sources"
                        result = await client.chat.send_message(notebook_id, full_query)
                        cluster.raw_answer = result.text
                    except AttributeError:
                        # Fallback for alternative method
                        full_query = f"Give everything you find about {cluster.query} from the sources"
                        result = await client.chat.ask(notebook_id, full_query)
                        cluster.raw_answer = result.answer

                    logger.info(f"Cluster {cluster.cluster_id}: got {len(cluster.raw_answer)} chars")
                    if tracker:
                        tracker.set_activity(
                            "Got answer from NotebookLM",
                            cluster_info=f"[{i+1}/{len(clusters)}] {short_topics}",
                        )

                # Follow-up query
                if cluster.follow_up_query and not cluster.follow_up_answer:
                    if tracker:
                        tracker.set_activity(
                            "Asking follow-up query...",
                            cluster_info=f"[{i+1}/{len(clusters)}] {short_topics}",
                        )
                    logger.info(f"Follow-up for cluster {cluster.cluster_id}")
                    
                    try:
                        result = await client.chat.send_message(notebook_id, cluster.follow_up_query)
                        cluster.follow_up_answer = result.text
                    except AttributeError:
                        result = await client.chat.ask(notebook_id, cluster.follow_up_query)
                        cluster.follow_up_answer = result.answer
                        
                    logger.info(f"Cluster {cluster.cluster_id} follow-up: got {len(cluster.follow_up_answer)} chars")
                    if tracker:
                        tracker.set_activity(
                            "Got follow-up answer",
                            cluster_info=f"[{i+1}/{len(clusters)}] {short_topics}",
                        )

    except Exception as e:
        error_msg = f"Retriever error during query: {e}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        # Don't raise here to allow pipeline to proceed with what we got

    return state
