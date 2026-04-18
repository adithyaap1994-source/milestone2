# Phase-Wise RAG Architecture: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## 1) Objective and Compliance Contract

This architecture is designed to satisfy the problem statement requirements:

- Facts-only responses from verified sources
- Mandatory source citation + last updated date in every answer
- Explicit refusal for advisory/recommendation queries
- Support for multiple concurrent chat threads
- Trust, transparency, and auditability over open-ended intelligence

Mandatory disclaimer in all final responses:

> Facts-only. No investment advice.

## 2) Scope and Ground Rules

- Domain: Mutual fund FAQs for selected AMC/schemes
- Data policy: only approved URLs and documents
- Source transparency: every response must include source URL and update date
- PDF policy (current): can be onboarded in later phase if parser quality gates pass
- Architecture style: modular services with phase-wise rollout and measurable gates

### In-Scope URLs (Current Registry)

The following URLs are approved for this milestone:

- `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth`
- `https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth`
- `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund/direct`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/regular`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver/direct`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver/regular`
- `https://www.hdfcfund.com/explore/mutual-funds/hdfc-mid-cap-fund/direct`
- `https://www.hdfcfund.com/mutual-funds/fund-documents/kim`
- `https://www.hdfcfund.com/mutual-funds/factsheets`
- `https://www.hdfcfund.com/statutory-disclosure/total-expense-ratio-of-mutual-fund-schemes/reports`
- `https://www.hdfcfund.com/statutory-disclosure/portfolio/monthly-portfolio`
- `https://www.hdfcfund.com/statutory-disclosure`
- `https://www.hdfcfund.com/learn/blog/how-get-capital-gain-statement-mutual-fund-schemes-india`

### PDF Scope Note (Current)

- Currently, PDFs are not being provided/ingested in this milestone.
- The following SID PDF URLs are identified for future onboarding only:
  - `https://files.hdfcfund.com/s3fs-public/SID/2025-05/SID%20-%20HDFC%20Large%20Cap%20Fund%20dated%20May%2030,%202025.pdf`
  - `https://files.hdfcfund.com/s3fs-public/SID/2024-06/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20June%2028,%202024.pdf`
  - `https://files.hdfcfund.com/s3fs-public/SID/2024-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20Fund%20dated%20November%2021,%202024.pdf`

## 3) Target End-State Architecture (After All Phases)

```text
User -> Chat API -> Orchestrator -> (Intent + Policy Guardrails)
                               -> Hybrid Retrieval (Vector + BM25 + Reranker)
                               -> Answer Composer (Citation Contract)
                               -> Response Validator (facts-only checks)

Ingestion Plane:
Source Registry -> Scheduler -> Scraper -> Normalizer -> Chunker -> Embedder
                -> Index Upsert (Vector + Keyword) -> Observability + Reports

State Plane:
Thread Store + Message Store + Audit Logs + Metrics
```

---

## 4) Phase 1: Foundation (Data, Retrieval Base, Transparency Baseline)

### Goal

Build the ingestion and retrieval foundation so factual answers can be generated with reliable citations.

### Components in Phase 1

1. **Source Registry**
   - Curated in-scope URLs per scheme/source type
2. **Scheduler**
   - GitHub Actions runs every day at **9:15 AM** to fetch the latest data.
   - Scheduler trigger is responsible for starting the full ingestion workflow.
3. **Scraping Service**
   - Get data from the approved in-scope URLs.
   - Fetch and parse HTML pages URL-by-URL, then pass extracted content to normalization.
   - Retry and failure-safe behavior
4. **Normalization Service**
   - Clean text, preserve key facts and metadata
5. **Chunking Service**
   - Semantic/token-aware chunking with overlap
6. **Embedding Service**
   - Chunk-level embeddings using pinned model `bge-small-en-v1.5`
7. **Hybrid Index Builder**
   - Vector payload + keyword/BM25 payload generation
8. **Local Retrieval Artifacts**
   - Persist vector and keyword payloads locally for retrieval services
9. **Run Reports**
   - Source fetch outcomes, chunk stats, index row counts

### Data Flow

```text
GitHub Actions (every day 9:15 AM, latest data refresh) ->
Load source registry ->
Scrape approved URLs ->
Normalize ->
Chunk ->
Embed ->
Build vector + keyword index payloads ->
Persist local vector/keyword payloads ->
Publish run report
```

### Scheduler Service Architecture (GitHub Actions)

- Platform: GitHub Actions (`.github/workflows/daily-ingestion.yml`)
- Trigger:
  - Scheduled run every day at 9:15 AM (IST-aligned schedule)
  - Manual trigger using `workflow_dispatch` for reruns/backfills
- Job stages:
  1. Checkout repository and install dependencies
  2. Load source registry and run scraping
  3. Run chunking and embedding pipeline
  4. Build keyword payload and vector payload
  5. Persist vectors and metadata as local retrieval artifacts
  6. Publish run summary artifact/log
- Reliability controls:
  - `concurrency` group to prevent overlapping runs
  - retry for transient fetch/provider failures
  - failure alerts and run logs for debugging

### Separate Architecture: Chunking and Embedding

This is an independent processing layer after normalization and before index upsert.

#### A) Chunking Architecture

1. **Input contract**
   - Receives normalized documents with:
     - `doc_id`, `source_url`, `scheme_name`, `section_title`, `content`, `last_updated`
2. **Pre-processing**
   - Clean whitespace and remove boilerplate fragments
   - Preserve numeric and date-bearing lines for factual integrity
3. **Segmentation strategy**
   - Token-aware chunking with semantic boundary preference
   - Target chunk size: 700 tokens
   - Overlap: 100 tokens
   - Range: 500-900 tokens (adaptive)
4. **Context carry-forward**
   - Prefix each chunk with section title/scheme metadata
   - Preserve source URL linkage in each chunk record
5. **Chunk ID generation**
   - Deterministic `chunk_id` from `doc_id + chunk_index + chunk_text_hash`
6. **Chunk quality checks**
   - Non-empty chunk text
   - Valid token count
   - Metadata completeness (`source_url`, `scheme_name`, `last_updated` nullable with reason)

#### B) Embedding Architecture

1. **Input contract**
   - Receives validated chunk records from chunking stage
2. **Model control**
   - Use pinned embedding model `bge-small-en-v1.5` (no silent model drift)
   - Store `embedding_model_version` in every chunk metadata row
3. **Embedding execution**
   - Batch embedding requests for throughput (e.g., 32-128 chunks/batch)
   - Retry with exponential backoff on transient failures/rate limits
4. **Validation**
   - Vector dimension check for every embedding
   - Null/NaN guard checks
   - Embedding count must equal chunk count
5. **Re-embedding policy**
   - Re-embed only when:
     - chunk content changes (`content_hash` change), or
     - model version changes, or
     - chunking strategy version changes

#### C) Index Handoff (Post-Embedding)

- Vector payload:
  - `chunk_id`, `vector`, compact metadata (`scheme_name`, `source_type`, `last_updated`)
- Keyword payload:
  - `chunk_id`, `chunk_text`, full metadata for BM25 retrieval
- Local vector payload target:
  - File: `data/index/vector_payload.jsonl`
  - `chunk_id`, `vector`, and compact retrieval metadata
- Atomic activation rule:
  - document is considered active only after local vector and keyword payload generation both succeed

#### E) Local Retrieval Configuration

- Deployment choice: local retrieval artifacts generated by ingestion
- Runtime outputs:
  - `data/index/vector_payload.jsonl`
  - `data/index/keyword_payload.jsonl`
- Access pattern:
  - Ingestion pipeline writes local payload files.
  - Query services read payloads and apply keyword/vector scoring as needed.
- Idempotency:
  - Stable `chunk_id` values let daily reruns update records safely.
- Failure policy:
  - If payload generation fails, mark run as partial failure and keep previous indexed state active.

#### D) Operational Metrics for Chunk+Embed

- Chunk generation success rate
- Average chunks per document
- Embedding success rate
- Mean embedding latency per batch
- Documents skipped due to unchanged hash
- Index upsert success/failure counts

### Phase 1 Output Artifacts

- Source registry
- Raw HTML snapshots
- Normalized documents
- Chunk records
- Embedding payloads
- Vector and keyword index payloads
- Local retrieval payload generation summary (success/failure counts)
- Daily ingestion report

### Phase 1 Quality Gates

- >= 95% source fetch success on active URLs
- 100% normalized docs have source URL metadata
- 100% chunks have non-empty text
- 100% index rows include provenance fields
- Run report generated on every scheduler execution

### Known Limitations in Phase 1

- No full conversational policy engine yet
- Advisory refusal may be basic/rule-based
- UI may be minimal
- Retrieval quality tuning still pending

---

## 5) Phase 2: Compliance + Conversation Intelligence

### Goal

Add strict policy controls and robust multi-thread chat behavior while keeping facts-only contract intact.

### Components in Phase 2

1. **Intent Classifier**
   - `factual_query` vs `advisory_query` vs `out_of_scope`
2. **Advisory Refusal Engine**
   - Standard refusal template
   - No recommendation/prediction output
3. **Response Validator**
   - Enforce presence of source links + last updated
   - Block responses failing citation contract
4. **Thread Manager**
   - `thread_id` scoped context
   - No context leakage across threads
5. **Message Persistence**
   - Store user/assistant messages with citation metadata
6. **Prompt Contract Layer**
   - Strict answer format:
     - factual answer
     - sources
     - last updated
     - disclaimer

### Data Flow (Query Time)

```text
User query + thread_id ->
Intent classification ->
if advisory => refusal response
else -> hybrid retrieval -> answer generation from evidence ->
response validator -> store response + citations
```

### Phase 2 Quality Gates

- >= 98% advisory refusal correctness on test set
- >= 99% responses include valid source citation fields
- 0 cross-thread context leakage incidents
- >= 95% format compliance with response schema

### Phase 2 Deliverables

- Compliance policy module
- Multi-thread chat data model
- Response validator
- Benchmark prompts (factual + advisory + edge cases)

---

## 6) Phase 3: Optimization, Evaluation, and Production Readiness

### Goal

Improve retrieval accuracy and reliability to production-grade standards with observability and release gates.

### Components in Phase 3

1. **Retrieval Optimization**
   - Query rewriting
   - Reranking and score calibration
   - Better metadata filtering
2. **Evaluation Framework**
   - Offline benchmark set
   - Factual accuracy and citation validity scoring
3. **Observability Stack**
   - Dashboards for citation rate, refusal quality, ingestion health
   - Alerts for failures and stale data
4. **Release Gates**
   - Block deployment if metrics fall below thresholds
5. **Operational Hardening**
   - Retry strategy tuning
   - Runbooks and incident workflow

### Phase 3 Quality Gates

- Factual accuracy >= 95% (benchmark set)
- Citation validity >= 99%
- Hallucination rate <= 2%
- Advisory leakage near-zero
- Freshness SLA met for scheduled updates

### Phase 3 Deliverables

- Evaluation suite + reports
- Monitoring dashboards and alerts
- Production runbook
- Release checklist with metric thresholds

---

## 7) Cross-Phase Data Model (Core Entities)

1. **Source**
   - URL, source type, AMC, scheme, active flag
2. **Document**
   - doc id, source URL, content hash, last updated, metadata
3. **Chunk**
   - chunk id, doc id, chunk text, token count, section metadata
4. **Embedding**
   - chunk id, vector, model version
5. **Thread**
   - thread id, user/session id, timestamps
6. **Message**
   - thread id, role, text, citations, policy decision
7. **Audit Event**
   - request id, retrieval set, policy result, validation status

## 8) Response Schema (Must be Consistent Across Phases)

1. **Answer** (facts from retrieved evidence only)
2. **Sources** (URL list)
3. **Last Updated** (date per source or explicit unavailable marker)
4. **Disclaimer** (`Facts-only. No investment advice.`)

## 9) Suggested Implementation Milestones

### Sprint A (Phase 1)

- Source registry + scheduler + ingestion + chunk/embed/index baseline

### Sprint B (Phase 2)

- Advisory classifier/refusal + thread store + response validator

### Sprint C (Phase 3)

- Retrieval tuning + evaluation harness + observability + release gates

## 10) Traceability to Problem Statement

- **Transparency** -> Mandatory source + last updated in schema and validator
- **Facts-only** -> policy guardrails and response contract
- **No advice** -> advisory detection and refusal engine
- **Multiple threads** -> thread-scoped context and storage model
- **Accurate retrieval** -> phased hybrid retrieval + reranking + evaluation

This phase-wise plan keeps implementation practical while ensuring compliance and trust are built into each stage rather than added later.
