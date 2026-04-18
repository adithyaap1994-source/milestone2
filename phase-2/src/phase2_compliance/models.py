from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Intent = Literal["factual_query", "advisory_query", "out_of_scope"]


@dataclass
class Citation:
    source_url: str
    last_updated: Optional[str]


@dataclass
class Message:
    thread_id: str
    role: Literal["user", "assistant"]
    content: str
    intent: Optional[Intent] = None
    policy_decision: Optional[str] = None
    citations: List[Citation] = field(default_factory=list)


@dataclass
class ResponsePayload:
    answer: str
    sources: List[str]
    last_updated: List[str]
    disclaimer: str = "Facts-only. No investment advice."
    policy_decision: str = "answer"


@dataclass
class ThreadState:
    thread_id: str
    messages: List[Message]
    metadata: Dict[str, str] = field(default_factory=dict)
