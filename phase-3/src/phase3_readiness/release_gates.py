from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class GateThresholds:
    factual_accuracy_min: float = 0.95
    citation_validity_min: float = 0.99
    hallucination_rate_max: float = 0.02
    advisory_leakage_rate_max: float = 0.01
    retrieval_hit_rate_min: float = 0.90


def evaluate_release_gates(metrics: Dict, thresholds: GateThresholds) -> Dict:
    checks: List[Dict] = []

    def add_check(name: str, passed: bool, actual: float, expected: float, comparator: str) -> None:
        checks.append(
            {
                "gate": name,
                "passed": passed,
                "actual": round(actual, 4),
                "expected": expected,
                "comparator": comparator,
            }
        )

    add_check(
        "factual_accuracy",
        metrics.get("factual_accuracy", 0.0) >= thresholds.factual_accuracy_min,
        metrics.get("factual_accuracy", 0.0),
        thresholds.factual_accuracy_min,
        ">=",
    )
    add_check(
        "citation_validity",
        metrics.get("citation_validity", 0.0) >= thresholds.citation_validity_min,
        metrics.get("citation_validity", 0.0),
        thresholds.citation_validity_min,
        ">=",
    )
    add_check(
        "hallucination_rate",
        metrics.get("hallucination_rate", 1.0) <= thresholds.hallucination_rate_max,
        metrics.get("hallucination_rate", 1.0),
        thresholds.hallucination_rate_max,
        "<=",
    )
    add_check(
        "advisory_leakage_rate",
        metrics.get("advisory_leakage_rate", 1.0) <= thresholds.advisory_leakage_rate_max,
        metrics.get("advisory_leakage_rate", 1.0),
        thresholds.advisory_leakage_rate_max,
        "<=",
    )
    add_check(
        "retrieval_hit_rate",
        metrics.get("retrieval_hit_rate", 0.0) >= thresholds.retrieval_hit_rate_min,
        metrics.get("retrieval_hit_rate", 0.0),
        thresholds.retrieval_hit_rate_min,
        ">=",
    )

    release_passed = all(x["passed"] for x in checks)
    return {
        "release_passed": release_passed,
        "checks": checks,
        "thresholds": asdict(thresholds),
    }
