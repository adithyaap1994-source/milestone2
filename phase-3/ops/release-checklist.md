# Phase 3 Release Checklist

- Run `python run_phase3.py`
- Confirm `reports/evaluation_report.json` exists
- Confirm `reports/release_gate_report.json` exists
- Confirm `reports/monitoring_metrics.json` exists
- Verify all release gates are passing
- Verify disclaimer contract remains unchanged:
  - `Facts-only. No investment advice.`
- Verify source citation and last-updated checks remain enabled
- Verify scheduler status and last successful ingestion
- Review open incidents/alerts before deployment
