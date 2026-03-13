"""Node 3: EVALUATOR — GLM-5 checks depth, triggers follow-up if needed."""

from __future__ import annotations

import json
import logging
from typing import Literal

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from config import OLLAMA_MODEL, OLLAMA_BASE_URL, MAX_RETRIEVAL_DEPTH, MIN_ANSWER_LENGTH
from core.state import SAGEState
from prompts.evaluator_prompt import EVALUATOR_SYSTEM_PROMPT

logger = logging.getLogger("sage.evaluator")


async def evaluator_node(state: SAGEState, config: RunnableConfig = None) -> SAGEState:
    """
    Evaluate retrieved content for depth and generate follow-up queries if needed.
    """
    tracker = None
    if config and "metadata" in config and "tracker" in config["metadata"]:
        tracker = config["metadata"]["tracker"]

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.2,
        format="json",
    )

    for i, cluster in enumerate(state["clusters"]):
        state["current_cluster_idx"] = i  # Update progress for UI

        topics_str = ", ".join(cluster.topics)
        short_topics = topics_str[:35] + ("..." if len(topics_str) > 35 else "")

        if tracker:
            tracker.set_activity(
                "Evaluating answer depth...",
                cluster_info=f"[{i+1}/{len(state['clusters'])}] {short_topics}",
            )

        if cluster.is_deep_enough:
            continue

        answer = cluster.raw_answer or ""

        # Quick length check first
        if len(answer) < MIN_ANSWER_LENGTH:
            logger.info(
                f"Cluster {cluster.cluster_id}: answer too short "
                f"({len(answer)} < {MIN_ANSWER_LENGTH} chars)"
            )
            cluster.is_deep_enough = False
            cluster.follow_up_query = (
                f"I need more detailed information about {', '.join(cluster.topics)}. "
                f"Please provide: detailed mechanics and internal workings, "
                f"concrete examples with step-by-step walkthroughs, "
                f"mathematical formulations if applicable, "
                f"and common exam questions with answers."
            )
            continue

        # Full LLM evaluation for longer answers
        user_message = (
            f"Topics: {', '.join(cluster.topics)}\n\n"
            f"Answer to evaluate:\n{answer}"
        )

        try:
            response = await llm.ainvoke([
                SystemMessage(content=EVALUATOR_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            cluster.is_deep_enough = result.get("is_deep_enough", True)

            if not cluster.is_deep_enough:
                cluster.follow_up_query = result.get("follow_up_query")
                logger.info(
                    f"Cluster {cluster.cluster_id}: needs follow-up"
                )
            else:
                logger.info(
                    f"Cluster {cluster.cluster_id}: deep enough ✓"
                )

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                f"Evaluator parse error for cluster {cluster.cluster_id}: {e}. "
                f"Marking as deep enough to avoid blocking."
            )
            cluster.is_deep_enough = True

    return state


def evaluator_edge(state: SAGEState) -> Literal["more_info", "sufficient"]:
    """
    LangGraph conditional edge to determine next steps.
    Returns "more_info" if any cluster needs follow-up, else "sufficient".
    """
    for cluster in state["clusters"]:
        # If it's shallow AND we have a query AND we haven't answered it yet
        if not cluster.is_deep_enough and cluster.follow_up_query and not cluster.follow_up_answer:
            return "more_info"
            
    return "sufficient"
