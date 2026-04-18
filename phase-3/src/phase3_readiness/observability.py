from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


def build_monitoring_metrics(evaluation_summary: Dict, release_gate_report: Dict) -> Dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "retrieval_hit_rate": evaluation_summary.get("retrieval_hit_rate"),
            "factual_accuracy": evaluation_summary.get("factual_accuracy"),
            "citation_validity": evaluation_summary.get("citation_validity"),
            "hallucination_rate": evaluation_summary.get("hallucination_rate"),
            "advisory_leakage_rate": evaluation_summary.get("advisory_leakage_rate"),
        },
        "release_status": "pass" if release_gate_report.get("release_passed") else "fail",
        "alerts": [
            {
                "name": check["gate"],
                "severity": "high",
                "message": f"Gate failed: {check['gate']}",
            }
            for check in release_gate_report.get("checks", [])
            if not check.get("passed")
        ],
    }
