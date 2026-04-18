from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

def _load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def rewrite_query(query: str) -> str:
    q = query.lower().strip()
    replacements = {
        "ter": "total expense ratio",
        "nav": "net asset value",
        "elss": "elss tax saver",
    }
    for src, dst in replacements.items():
        q = re.sub(rf"\b{re.escape(src)}\b", dst, q)
    return q


def _token_overlap_score(query: str, text: str) -> float:
    q_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    t_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    if not q_tokens or not t_tokens:
        return 0.0
    overlap = len(q_tokens.intersection(t_tokens))
    return overlap / len(q_tokens)


def _metadata_boost(query: str, metadata: Dict) -> float:
    query_lower = query.lower()
    boost = 0.0
    scheme = (metadata.get("scheme_name") or "").lower()
    source_type = (metadata.get("source_type") or "").lower()

    if scheme and any(token in scheme for token in query_lower.split()):
        boost += 0.25
    if "expense ratio" in query_lower and "statutory" in source_type:
        boost += 0.20
    if "factsheet" in query_lower and "factsheet" in source_type:
        boost += 0.20
    return boost


def optimized_retrieve(project_root: Path, query: str, top_k: int = 5) -> List[Dict]:
    keyword_path = project_root / "phase-1" / "data" / "index" / "keyword_payload.jsonl"
    rows = _load_jsonl(keyword_path)
    rewritten = rewrite_query(query)
    # Local keyword payload scoring.
    if not rows:
        return []

    scored: List[Dict] = []
    for row in rows:
        text = row.get("text", "")
        metadata = row.get("metadata", {})
        base = _token_overlap_score(rewritten, text)
        score = base + _metadata_boost(rewritten, metadata)
        scored.append(
            {
                "chunk_id": row.get("chunk_id"),
                "score": round(score, 6),
                "text": text,
                "metadata": metadata,
            }
        )

    # Lightweight reranking: relevance score first, then prefer sources with explicit URL.
    scored.sort(key=lambda r: (r["score"], bool(r["metadata"].get("source_url"))), reverse=True)
    return scored[:top_k]
