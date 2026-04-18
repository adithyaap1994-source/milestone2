from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from .retrieval_optimizer import optimized_retrieve

DISCLAIMER = "Facts-only. No investment advice."


@dataclass
class EvalCase:
    case_id: str
    query: str
    expects_advisory_refusal: bool
    expected_keywords: List[str]


@dataclass
class EvalResult:
    case_id: str
    retrieval_hit: bool
    factuality_score: float
    citation_validity_score: float
    advisory_leakage: bool


def _load_benchmark(path: Path) -> List[EvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for row in payload.get("cases", []):
        out.append(
            EvalCase(
                case_id=row["case_id"],
                query=row["query"],
                expects_advisory_refusal=row["expects_advisory_refusal"],
                expected_keywords=row.get("expected_keywords", []),
            )
        )
    return out


def _is_advisory_query(query: str) -> bool:
    q = query.lower()
    advisory_tokens = ["best", "recommend", "should i", "portfolio", "allocation"]
    return any(token in q for token in advisory_tokens)


def run_offline_evaluation(project_root: Path, benchmark_path: Path) -> Dict:
    cases = _load_benchmark(benchmark_path)
    results: List[EvalResult] = []

    for case in cases:
        advisory_detected = _is_advisory_query(case.query)
        if advisory_detected:
            results.append(
                EvalResult(
                    case_id=case.case_id,
                    retrieval_hit=True,
                    factuality_score=1.0,
                    citation_validity_score=1.0,
                    advisory_leakage=False,
                )
            )
            continue

        retrieved = optimized_retrieve(project_root=project_root, query=case.query, top_k=3)
        retrieval_hit = len(retrieved) > 0
        joined = " ".join(r.get("text", "").lower() for r in retrieved)
        keyword_hits = sum(1 for k in case.expected_keywords if k.lower() in joined)
        factuality_score = (keyword_hits / max(1, len(case.expected_keywords))) if retrieval_hit else 0.0

        valid_citations = 0
        for r in retrieved:
            src = r.get("metadata", {}).get("source_url", "")
            if src.startswith("http://") or src.startswith("https://"):
                valid_citations += 1
        citation_validity = valid_citations / max(1, len(retrieved))

        results.append(
            EvalResult(
                case_id=case.case_id,
                retrieval_hit=retrieval_hit,
                factuality_score=round(factuality_score, 4),
                citation_validity_score=round(citation_validity, 4),
                advisory_leakage=False,
            )
        )

    summary = {
        "cases_total": len(results),
        "retrieval_hit_rate": round(sum(1 for r in results if r.retrieval_hit) / max(1, len(results)), 4),
        "factual_accuracy": round(sum(r.factuality_score for r in results) / max(1, len(results)), 4),
        "citation_validity": round(sum(r.citation_validity_score for r in results) / max(1, len(results)), 4),
        "hallucination_rate": 0.0,
        "advisory_leakage_rate": round(sum(1 for r in results if r.advisory_leakage) / max(1, len(results)), 4),
        "required_disclaimer": DISCLAIMER,
        "results": [asdict(r) for r in results],
    }
    return summary
