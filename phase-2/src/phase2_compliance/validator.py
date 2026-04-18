from __future__ import annotations

from typing import List

from .models import ResponsePayload

REQUIRED_DISCLAIMER = "Facts-only. No investment advice."


def validate_response(payload: ResponsePayload) -> List[str]:
    errors: List[str] = []

    if not payload.answer.strip():
        errors.append("Empty answer body.")

    if payload.policy_decision == "answer":
        if not payload.sources:
            errors.append("Missing source URLs for factual response.")
        if not payload.last_updated:
            errors.append("Missing last updated fields for factual response.")
        if len(payload.sources) != len(payload.last_updated):
            errors.append("Sources and last_updated lengths do not match.")
        for url in payload.sources:
            if not (url.startswith("http://") or url.startswith("https://")):
                errors.append(f"Invalid source URL format: {url}")

    if payload.disclaimer != REQUIRED_DISCLAIMER:
        errors.append("Invalid disclaimer text.")

    return errors
