# Phase 3 Production Runbook

## Purpose

Operational guide for retrieval quality, evaluation health, and release gating.

## Routine Operations

1. Ensure daily Phase 1 ingestion completed successfully.
2. Run Phase 3 evaluation:
   - `cd phase-3`
   - `python run_phase3.py`
3. Review:
   - factual accuracy
   - citation validity
   - hallucination rate
   - advisory leakage rate
4. Confirm release-gate pass before production release.

## Incident Handling

### Retrieval hit rate drop

- Check latest `phase-1/data/index/keyword_payload.jsonl` presence and size.
- Re-run Phase 1 ingestion.
- Re-run Phase 3 evaluation and compare metrics.

### Citation validity drop

- Check source URL fields in index payloads.
- Verify response validator still enforces source and date fields.

### Advisory leakage incident

- Review intent classifier and refusal keywords.
- Add failing prompt to benchmark set.
- Re-run evaluation and verify gate results.

## Rollback Guidance

- If release gates fail, block deployment.
- Keep previous known-good model/index snapshot active.
- Open incident ticket with root cause and mitigation plan.
