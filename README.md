# Mutual Fund FAQ Assistant

This repository is organized by implementation phase based on `docs/phase-wise-rag-architecture.md`.

## Folder Structure

- `api/`: Vercel Python serverless (`api/index.py` — `handler` for `GET /api`)
- `phase-1/`: source registry + ingestion + chunking + bge embeddings + local retrieval artifacts
- `phase-2/`: compliance/policy + multi-thread conversation handling + citation retrieval
- `phase-3/`: retrieval optimization + evaluation + release gates + readiness ops
- `docs/`: architecture and problem statement

## Current Status

All three phases are implemented based on `docs/phase-wise-rag-architecture.md`.