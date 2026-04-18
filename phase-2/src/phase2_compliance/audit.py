from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


class AuditLogger:
    """Append-only JSONL audit log for policy and retrieval traceability."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: Dict) -> None:
        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
