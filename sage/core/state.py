"""SAGE state — LangGraph state definitions using TypedDict."""

from __future__ import annotations

from typing import Optional, TypedDict
from dataclasses import dataclass, field


@dataclass
class TopicCluster:
    cluster_id: int
    topics: list[str]
    query: str
    raw_answer: Optional[str] = None
    follow_up_query: Optional[str] = None
    follow_up_answer: Optional[str] = None
    is_deep_enough: bool = False
    notes_content: Optional[str] = None
    mermaid_code: Optional[str] = None


class SAGEState(TypedDict):
    subject: str
    unit_number: int
    unit_title: str
    all_topics: list[str]
    clusters: list[TopicCluster]
    infographic_path: Optional[str]
    current_cluster_idx: int
    errors: list[str]
    is_complete: bool