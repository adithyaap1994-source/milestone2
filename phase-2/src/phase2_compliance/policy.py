from __future__ import annotations

import re
from typing import List

from .models import Citation, Intent, ResponsePayload

ADVISORY_PATTERNS = [
    r"\bbest\b",
    r"\bbetter\b",
    r"\brecommend\b",
    r"\bshould i invest\b",
    r"\bwhich fund\b",
    r"\bportfolio\b",
    r"\ballocation\b",
    r"\bhigh return\b",
    r"\bsafe option\b",
    r"\bbuy\b",
    r"\bsell\b",
]

OUT_OF_SCOPE_PATTERNS = [
    r"\bweather\b",
    r"\bmovie\b",
    r"\bcricket score\b",
    r"\brecipe\b",
]


def classify_intent(user_query: str) -> Intent:
    text = user_query.lower()
    if any(re.search(p, text) for p in ADVISORY_PATTERNS):
        return "advisory_query"
    if any(re.search(p, text) for p in OUT_OF_SCOPE_PATTERNS):
        return "out_of_scope"
    return "factual_query"


def refusal_payload(reason: str = "advisory") -> ResponsePayload:
    if reason == "out_of_scope":
        answer = (
            "I can only provide factual information about mutual fund schemes from approved sources. "
            "This request is out of scope."
        )
        policy_decision = "out_of_scope_refusal"
    else:
        answer = (
            "I can only provide factual information from approved mutual fund sources. "
            "I cannot provide investment advice or recommendations."
        )
        policy_decision = "advisory_refusal"

    return ResponsePayload(
        answer=answer,
        sources=[],
        last_updated=[],
        policy_decision=policy_decision,
    )


def build_factual_response(answer: str, citations: List[Citation]) -> ResponsePayload:
    return ResponsePayload(
        answer=answer.strip(),
        sources=[c.source_url for c in citations],
        last_updated=[c.last_updated if c.last_updated else "Not available in source" for c in citations],
        policy_decision="answer",
    )
