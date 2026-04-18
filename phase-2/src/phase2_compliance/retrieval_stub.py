from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import Citation


def _load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def retrieve_citations_for_query(query: str, project_root: Path, top_k: int = 2) -> List[Citation]:
    """Retrieve citations using local keyword payload only."""
    keyword_path = project_root / "phase-1" / "data" / "index" / "keyword_payload.jsonl"
    rows = _load_jsonl(keyword_path)
    if not rows:
        return []

    query_words = set(query.lower().split())
    scored = []
    for row in rows:
        text = row.get("text", "").lower()
        score = sum(1 for w in query_words if w in text)
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)

    citations: List[Citation] = []
    seen = set()
    for _, row in scored:
        src = row.get("metadata", {}).get("source_url")
        if not src or src in seen:
            continue
        seen.add(src)
        citations.append(Citation(source_url=src, last_updated="Not available in source"))
        if len(citations) >= top_k:
            break
    return citations
