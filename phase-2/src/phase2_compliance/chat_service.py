from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict
from uuid import uuid4

from .audit import AuditLogger

from .models import Message
from .policy import build_factual_response, classify_intent, refusal_payload
from .retrieval_stub import retrieve_citations_for_query
from .thread_store import ThreadStore
from .validator import validate_response


class ComplianceChatService:
    def __init__(self, project_root: Path, thread_store_path: Path) -> None:
        self.project_root = project_root
        self.store = ThreadStore(thread_store_path)
        self.audit = AuditLogger(thread_store_path.parent / "audit_log.jsonl")

    def handle_user_message(self, thread_id: str, user_query: str) -> Dict:
        request_id = str(uuid4())
        intent = classify_intent(user_query)
        self.store.append_message(
            Message(thread_id=thread_id, role="user", content=user_query, intent=intent, policy_decision="received")
        )

        citations = []
        if intent == "advisory_query":
            payload = refusal_payload(reason="advisory")
        elif intent == "out_of_scope":
            payload = refusal_payload(reason="out_of_scope")
        else:
            citations = retrieve_citations_for_query(user_query, self.project_root)
            if not citations:
                payload = refusal_payload(reason="out_of_scope")
                payload.answer = (
                    "I could not find enough approved factual evidence for this query in the indexed sources. "
                    "Please rephrase using scheme-specific terms."
                )
                payload.policy_decision = "insufficient_evidence"
            else:
                answer = (
                    "Based on currently indexed approved sources, here is the factual information available for your query. "
                    "Use the cited links to verify details."
                )
                payload = build_factual_response(answer=answer, citations=citations)

        errors = validate_response(payload)
        if errors:
            payload.answer = (
                "I am unable to return a compliant response right now because response validation failed. "
                "Please try again."
            )
            payload.sources = []
            payload.last_updated = []
            payload.policy_decision = "validation_failed"

        self.store.append_message(
            Message(
                thread_id=thread_id,
                role="assistant",
                content=payload.answer,
                policy_decision=payload.policy_decision,
                citations=[{"source_url": s, "last_updated": d} for s, d in zip(payload.sources, payload.last_updated)],
            )
        )
        self.audit.log_event(
            {
                "request_id": request_id,
                "thread_id": thread_id,
                "intent": intent,
                "policy_decision": payload.policy_decision,
                "query": user_query,
                "retrieval_count": len(citations),
                "response_validation_passed": len(errors) == 0,
                "validation_errors": errors,
                "sources": payload.sources,
            }
        )

        thread_state = self.store.get_thread(thread_id)
        return {
            "request_id": request_id,
            "thread_id": thread_id,
            "intent": intent,
            "response": asdict(payload),
            "messages_in_thread": len(thread_state.messages),
        }
