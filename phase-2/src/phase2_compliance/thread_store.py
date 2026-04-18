from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from .models import Message, ThreadState


class ThreadStore:
    """Simple file-backed thread store for Phase 2."""

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._lock = threading.RLock()
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self.data_path.write_text("{}", encoding="utf-8")

    def _read(self) -> Dict[str, Dict]:
        with self._lock:
            return json.loads(self.data_path.read_text(encoding="utf-8"))

    def _write(self, state: Dict[str, Dict]) -> None:
        with self._lock:
            self.data_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    def create_thread(self, thread_id: str) -> None:
        with self._lock:
            state = json.loads(self.data_path.read_text(encoding="utf-8"))
            state.setdefault(thread_id, {"thread_id": thread_id, "messages": [], "metadata": {}})
            self.data_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    def append_message(self, message: Message) -> None:
        with self._lock:
            state = json.loads(self.data_path.read_text(encoding="utf-8"))
            thread = state.setdefault(message.thread_id, {"thread_id": message.thread_id, "messages": [], "metadata": {}})
            thread["messages"].append(asdict(message))
            self.data_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")

    def get_thread(self, thread_id: str) -> ThreadState:
        with self._lock:
            state = json.loads(self.data_path.read_text(encoding="utf-8"))
            thread = state.get(thread_id, {"thread_id": thread_id, "messages": [], "metadata": {}})
        messages: List[Message] = []
        for row in thread["messages"]:
            messages.append(
                Message(
                    thread_id=row["thread_id"],
                    role=row["role"],
                    content=row["content"],
                    intent=row.get("intent"),
                    policy_decision=row.get("policy_decision"),
                    citations=row.get("citations", []),
                )
            )
        return ThreadState(thread_id=thread_id, messages=messages, metadata=thread.get("metadata", {}))
