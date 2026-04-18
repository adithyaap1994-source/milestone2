from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml
from bs4 import BeautifulSoup
try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_MODEL_VERSION = "bge-small-en-v1.5"
FALLBACK_VECTOR_DIM = 64


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def _token_chunks(text: str, target: int = 700, overlap: int = 100) -> List[str]:
    words = text.split()
    if not words:
        return []
    out: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + target)
        out.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return out


def _fetch_html_with_retry(url: str, headers: Dict[str, str], attempts: int = 3, timeout: int = 30) -> Dict[str, Any]:
    last_error = ""
    for attempt_idx in range(attempts):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            return {
                "status": resp.status_code,
                "html": resp.text or "",
                "attempts_used": attempt_idx + 1,
                "error": "",
            }
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt_idx < attempts - 1:
                time.sleep(2**attempt_idx)
    return {
        "status": 0,
        "html": "",
        "attempts_used": attempts,
        "error": last_error or "unknown_fetch_error",
    }


def _fallback_embed(text: str, dim: int = FALLBACK_VECTOR_DIM) -> List[float]:
    """Generate deterministic lightweight embedding when ML model is unavailable."""
    vec = [0.0] * dim
    words = text.split()
    if not words:
        return vec
    for idx, token in enumerate(words):
        bucket = hash(token) % dim
        vec[bucket] += 1.0 + ((idx % 7) / 10.0)
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def run_phase1(base_dir: Path) -> Dict[str, int]:
    cfg_path = base_dir / "config" / "source_registry.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    sources = [x for x in cfg.get("sources", []) if x.get("active", True)]

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ua = {"User-Agent": "mf-faq-assistant-phase1/1.0"}
    raw_rows: List[Dict[str, Any]] = []
    norm_rows: List[Dict[str, Any]] = []
    chunk_rows: List[Dict[str, Any]] = []
    vector_rows: List[Dict[str, Any]] = []
    keyword_rows: List[Dict[str, Any]] = []

    raw_dir = base_dir / "data" / "raw"
    _ensure_dir(raw_dir)

    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME) if SentenceTransformer is not None else None
    embedding_model_version = EMBEDDING_MODEL_VERSION if embedder is not None else "fallback-hash-v1"

    for src in sources:
        url = src["source_url"]
        fetched_at = datetime.now(timezone.utc).isoformat()
        fetch_outcome = _fetch_html_with_retry(url=url, headers=ua, attempts=3, timeout=30)
        html = fetch_outcome["html"]
        status = fetch_outcome["status"]

        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        raw_file = raw_dir / f"{content_hash[:16]}.html"
        raw_file.write_text(html, encoding="utf-8")

        raw_rows.append(
            {
                "source_url": url,
                "source_type": src["source_type"],
                "amc_name": src["amc_name"],
                "scheme_name": src["scheme_name"],
                "fetched_at": fetched_at,
                "http_status": status,
                "fetch_attempts": fetch_outcome["attempts_used"],
                "fetch_error": fetch_outcome["error"],
                "html_path": str(raw_file),
                "content_hash": content_hash,
            }
        )

        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string or src["scheme_name"]) if soup.title else src["scheme_name"]
        text = " ".join(soup.get_text(" ", strip=True).split()) or "No parsable content."
        doc_id = hashlib.sha256(f"{url}|{content_hash}".encode("utf-8")).hexdigest()[:24]
        norm_rows.append(
            {
                "doc_id": doc_id,
                "source_url": url,
                "source_type": src["source_type"],
                "amc_name": src["amc_name"],
                "scheme_name": src["scheme_name"],
                "section_title": title[:150],
                "content": text,
                "content_hash": content_hash,
                "last_updated": None,
                "retrieval_tags": [],
            }
        )

        chunks = _token_chunks(text, target=700, overlap=100)
        chunk_texts: List[str] = []
        chunk_ids: List[str] = []
        for idx, ch in enumerate(chunks):
            chunk_text = f"{title[:150]}\n{ch}"
            chunk_id = hashlib.sha256(f"{doc_id}|{idx}|{chunk_text}".encode("utf-8")).hexdigest()[:24]
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk_text)
            chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "source_url": url,
                    "source_type": src["source_type"],
                    "amc_name": src["amc_name"],
                    "scheme_name": src["scheme_name"],
                    "section_title": title[:150],
                    "chunk_text": chunk_text,
                    "chunk_index": idx,
                    "token_count": len(ch.split()),
                    "content_hash": content_hash,
                    "last_updated": None,
                    "embedding_model_version": EMBEDDING_MODEL_VERSION,
                    "pipeline_run_id": run_id,
                }
            )

        if chunk_texts:
            if embedder is not None:
                vectors = [vec.tolist() for vec in embedder.encode(chunk_texts, normalize_embeddings=True)]
            else:
                vectors = [_fallback_embed(text) for text in chunk_texts]
            for idx, vec in enumerate(vectors):
                chunk_id = chunk_ids[idx]
                chunk_text = chunk_texts[idx]
                vector_rows.append(
                    {
                        "chunk_id": chunk_id,
                        "vector": vec,
                        "metadata": {
                            "chunk_id": chunk_id,
                            "doc_id": doc_id,
                            "source_url": url,
                            "source_type": src["source_type"],
                            "scheme_name": src["scheme_name"],
                            "last_updated": None,
                            "embedding_model_version": embedding_model_version,
                            "pipeline_run_id": run_id,
                        },
                    }
                )
                keyword_rows.append(
                    {
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "chunk_id": chunk_id,
                            "doc_id": doc_id,
                            "source_url": url,
                            "source_type": src["source_type"],
                            "scheme_name": src["scheme_name"],
                            "last_updated": None,
                            "embedding_model_version": embedding_model_version,
                            "pipeline_run_id": run_id,
                        },
                    }
                )

    _write_jsonl(base_dir / "data" / "normalized" / "normalized_documents.jsonl", norm_rows)
    _write_jsonl(base_dir / "data" / "chunks" / "chunks.jsonl", chunk_rows)
    _write_jsonl(base_dir / "data" / "index" / "vector_payload.jsonl", vector_rows)
    _write_jsonl(base_dir / "data" / "index" / "keyword_payload.jsonl", keyword_rows)
    report = {
        "run_id": run_id,
        "embedding_model": embedding_model_version,
        "sources_active": len(sources),
        "raw_docs": len(raw_rows),
        "normalized_docs": len(norm_rows),
        "chunks": len(chunk_rows),
        "vector_rows": len(vector_rows),
        "keyword_rows": len(keyword_rows),
        "http_failures": sum(1 for r in raw_rows if r["http_status"] == 0 or r["http_status"] >= 400),
        "retry_fetches": sum(1 for r in raw_rows if r.get("fetch_attempts", 1) > 1),
    }
    report_path = base_dir / "reports" / f"phase1_run_{run_id}.json"
    _ensure_dir(report_path.parent)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
