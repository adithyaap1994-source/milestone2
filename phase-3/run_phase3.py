from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PROJECT_ROOT = ROOT.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_readiness.evaluator import run_offline_evaluation  # noqa: E402
from phase3_readiness.observability import build_monitoring_metrics  # noqa: E402
from phase3_readiness.release_gates import GateThresholds, evaluate_release_gates  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def main() -> None:
    benchmark_path = ROOT / "benchmarks" / "offline_benchmark.json"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    evaluation = run_offline_evaluation(project_root=PROJECT_ROOT, benchmark_path=benchmark_path)
    gate_report = evaluate_release_gates(evaluation, GateThresholds())
    metrics = build_monitoring_metrics(evaluation, gate_report)

    _write_json(reports_dir / "evaluation_report.json", evaluation)
    _write_json(reports_dir / "release_gate_report.json", gate_report)
    _write_json(reports_dir / "monitoring_metrics.json", metrics)

    print("Phase 3 run complete.")
    print(json.dumps({"release_passed": gate_report["release_passed"], "reports_dir": str(reports_dir)}, indent=2))


if __name__ == "__main__":
    main()
