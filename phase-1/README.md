# Phase 1: Foundation (Data, Retrieval Base, Transparency Baseline)

This phase implements source registry, scraping, normalization, chunking, embedding, and index payload generation.

Embedding model used:

- `BAAI/bge-small-en-v1.5`
- Retrieval artifacts: local `vector_payload.jsonl` + `keyword_payload.jsonl`

## Quick Start

```bash
cd phase-1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_phase1.py
```

## Output

- `data/raw/`: raw HTML snapshots
- `data/normalized/`: normalized document JSONL
- `data/chunks/`: chunk JSONL
- `data/index/`: vector and keyword payload JSONL
- `reports/`: run report JSON
