"""LangGraph pipeline assembly for SAGE."""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import StateGraph, END

from core.state import SAGEState
from core.nodes.planner import planner_node
from core.nodes.retriever import retriever_node
from core.nodes.evaluator import evaluator_node, evaluator_edge
from core.nodes.writer import writer_node
from core.nodes.studio import studio_node
from core.nodes.publisher import publisher_node
from ui.progress import PipelineTracker

logger = logging.getLogger("sage.pipeline")


def _router(state: SAGEState) -> Literal["retriever", "studio"]:
    """Route to next cluster or finish with studio."""
    # This is a dummy router for now.
    # In a full loop refactor, we'd check current_cluster_idx < len(clusters).
    # For now, we'll stick to the linear pipeline but improve the tracker integration.
    return "retriever"


def create_pipeline() -> StateGraph:
    """Create and compile the LangGraph pipeline."""
    workflow = StateGraph(SAGEState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("studio", studio_node)
    workflow.add_node("publisher", publisher_node)

    # Define edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "retriever")
    
    # Retriever -> Evaluator
    workflow.add_edge("retriever", "evaluator")
    
    # Evaluator -> Retriever (if more info needed) OR Writer
    workflow.add_conditional_edges(
        "evaluator",
        evaluator_edge,
        {
            "more_info": "retriever",
            "sufficient": "writer",
        },
    )
    
    workflow.add_edge("writer", "studio")
    workflow.add_edge("studio", "publisher")
    workflow.add_edge("publisher", END)

    return workflow.compile()


async def run_pipeline(
    subject: str,
    unit_number: int,
    unit_title: str,
    topics: list[str],
    tracker: PipelineTracker,
) -> SAGEState:
    """Execute the pipeline with a live UI tracker."""
    pipeline = create_pipeline()

    initial_state: SAGEState = {
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

    final_state = initial_state
    
    config = {
        "configurable": {"thread_id": "sage_run"},
        "metadata": {"tracker": tracker}
    }
    
    try:
        async for event in pipeline.astream(initial_state, config):
            # event is a dict: {node_name: state_update}
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    # Merge updates manually for the tracker to see current progress
                    final_state.update(node_output)
                    
                    clusters = final_state.get("clusters", [])
                    all_topics = final_state.get("all_topics", [])

                    # Map state to UI
                    tracker.set_node_done(node_name.upper())
                    
                    # Log activity
                    if node_name == "planner":
                        tracker.set_activity(
                            f"Created {len(clusters)} clusters",
                            cluster_info=f"{len(all_topics)} topics total",
                        )
                    elif node_name == "retriever":
                        tracker.set_activity(
                            "Information retrieved from NotebookLM",
                            cluster_info=f"Processed all {len(clusters)} clusters",
                        )
                        tracker.set_progress(len(clusters)) # Topics processed = progress bar
                    elif node_name == "evaluator":
                        depth = sum(1 for c in clusters if c.is_deep_enough)
                        tracker.set_activity(
                            f"Evaluated {depth}/{len(clusters)} as deep enough",
                            depth_info="Analyzing follow-ups..."
                        )
                    elif node_name == "writer":
                        written = sum(1 for c in clusters if c.notes_content)
                        tracker.set_activity(
                            f"Written notes for {written}/{len(clusters)} clusters",
                        )
                    elif node_name == "studio":
                        path = final_state.get("infographic_path")
                        tracker.set_activity(
                            "Infographic generated" if path else "Skipped infographic",
                            cluster_info=f"Saved to: {path}" if path else ""
                        )
                    elif node_name == "publisher":
                        tracker.set_activity("All notes published to vault.")
                        final_state["is_complete"] = True

                # Determine which node is NEXT and mark as running
                # Conditional edges mean this is just a quick UI hint
                next_map = {
                    "planner": "RETRIEVER",
                    "retriever": "EVALUATOR",
                    "evaluator": "WRITER",
                    "writer": "STUDIO",
                    "studio": "PUBLISHER",
                }
                
                # If we need more info, we loop back to retriever
                # So we infer running node based on logic
                if node_name == "evaluator":
                    needs_follow_up = False
                    for c in clusters:
                        if not c.is_deep_enough and c.follow_up_query and not c.follow_up_answer:
                            needs_follow_up = True
                            break
                    if needs_follow_up:
                        tracker.set_node_running("RETRIEVER")
                    else:
                        tracker.set_node_running("WRITER")
                elif node_name in next_map:
                    tracker.set_node_running(next_map[node_name])
                    if next_map[node_name] == "RETRIEVER":
                        tracker.set_activity("Connecting to NotebookLM...", cluster_info="Launching browser engine")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}")
        final_state["errors"].append(str(e))
        # Mark currently running node as failed
        for node in tracker.NODES:
            if tracker._node_statuses[node] == "running":
                tracker.set_node_failed(node)

    return final_state