"""Node 1: PLANNER — one syllabus line = one cluster, with a generated query."""

from __future__ import annotations

import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from config import OLLAMA_MODEL, OLLAMA_BASE_URL
from core.state import SAGEState, TopicCluster

logger = logging.getLogger("sage.planner")


async def planner_node(state: SAGEState) -> SAGEState:
    """
    Create one cluster per syllabus line and generate a rich
    NotebookLM query for each.

    No LLM clustering — each line in the syllabus IS a cluster.
    The LLM is used only to expand each topic into a deep query.
    """
    subject = state.get("subject", "General")
    topics = state.get("all_topics", [])

    if not topics:
        logger.warning("No topics provided to planner")
        state["clusters"] = []
        return state

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3,
    )

    clusters: list[TopicCluster] = []

    for i, topic in enumerate(topics):
        topic = topic.strip().rstrip(",").rstrip(".")
        if not topic:
            continue

        # Generate a rich query for this single topic
        try:
            response = await llm.ainvoke([
                SystemMessage(content=(
                    f"You are a university professor preparing study material for {subject}. "
                    f"Given a topic, write ONE detailed query that would extract comprehensive "
                    f"information from a textbook. The query must ask for: definitions, mechanics, "
                    f"real-world examples, connections to other concepts, and common exam questions. "
                    f"Return ONLY the query text, nothing else."
                )),
                HumanMessage(content=f"Topic: {topic}"),
            ])
            query = response.content.strip()
            if not query or len(query) < 10:
                query = f"Explain {topic} in {subject} in depth. Include definitions, mechanisms, examples, and exam-style questions."
        except Exception as e:
            logger.warning(f"Query generation failed for '{topic}': {e}")
            query = f"Explain {topic} in {subject} in depth. Include definitions, mechanisms, examples, and exam-style questions."

        clusters.append(
            TopicCluster(
                cluster_id=i + 1,
                topics=[topic],
                query=query,
            )
        )
        logger.info(f"Cluster {i+1}: {topic}")

    state["clusters"] = clusters
    logger.info(f"Planner created {len(clusters)} clusters (1 per syllabus line)")
    return state
