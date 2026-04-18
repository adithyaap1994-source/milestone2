# Detailed RAG Architecture: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## 1) Objective

Build a Retrieval-Augmented Generation (RAG) assistant for mutual fund FAQs that:

- Returns only factual, source-backed information.
- Includes source URL and last-updated date in every answer.
- Refuses investment advice or opinion-based requests.
- Supports multiple concurrent chat threads.
- Maintains transparent and auditable behavior.

This architecture prioritizes **accuracy, traceability, and compliance** over open-ended conversational capability.

## 2) Core Principles

1. **Facts-only responses**
   - The assistant may only answer using retrieved documents and approved metadata.
2. **Mandatory citation contract**
   - Every response includes:
     - Source link(s)
     - `last_updated` date per source
3. **No advisory behavior**
   - Any advisory query (recommendation, prediction, allocation suggestion) is refused with a standard compliance template.
4. **Thread-safe conversations**
   - Multiple conversation threads are isolated and maintain their own history/context windows.
5. **Deterministic and auditable**
   - Prompting, retrieval, ranking, and response formatting are structured and logged for replay/debugging.

## 3) High-Level Architecture

```text
                   +----------------------------+
User Query ------> |  API Gateway / Chat API   |
                   +-------------+--------------+
                                 |
                                 v
                  +------------------------------+
                  | Query Orchestrator           |
                  | - classify intent            |
                  | - enforce policy             |
                  | - run retrieval pipeline     |
                  +------+-----------------------+
                         |
            +------------+------------+
            |                         |
            v                         v
 +------------------------+   +------------------------+
 | Conversation Store     |   | Compliance Guardrails  |
 | - thread_id            |   | - advisory detector    |
 | - message history      |   | - facts-only validator |
 +------------------------+   +------------------------+
                         |
                         v
               +------------------------+
               | Retrieval Layer        |
               | 1) query rewrite       |
               | 2) hybrid search       |
               | 3) reranking           |
               +-----------+------------+
                           |
                           v
               +------------------------+
               | Knowledge Indexes      |
               | - vector index         |
               | - keyword/BM25 index   |
               | - metadata store       |
               +-----------+------------+
                           |
                           v
               +------------------------+
               | Response Composer      |
               | - answer from evidence |
               | - mandatory citations  |
               | - refusal templates    |
               +-----------+------------+
                           |
                           v
                     Final Answer
```

## 4) Data Sources and Document Model

## Allowed Sources

Use only approved, public, verifiable sources such as:

- AMC official scheme pages
- Scheme Information Document (SID)
- Key Information Memorandum (KIM)
- Factsheets / NAV disclosures
- SEBI/AMFI references where applicable

## In-Scope URLs (Current)

The following URLs are the currently approved source registry for this milestone:

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

## PDF Scope Note (Current)

- PDF ingestion is currently out of scope for this iteration.
- SID PDFs identified for future onboarding (not currently ingested):
  - `https://files.hdfcfund.com/s3fs-public/SID/2025-05/SID%20-%20HDFC%20Large%20Cap%20Fund%20dated%20May%2030,%202025.pdf`
  - `https://files.hdfcfund.com/s3fs-public/SID/2024-06/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20June%2028,%202024.pdf`
  - `https://files.hdfcfund.com/s3fs-public/SID/2024-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20Fund%20dated%20November%2021,%202024.pdf`

## Normalized Document Schema

Each ingested chunk should preserve provenance:

- `doc_id`: unique identifier
- `source_url`: canonical URL
- `source_type`: SID | KIM | factsheet | FAQ | circular
- `amc_name`
- `scheme_name`
- `section_title`
- `content`
- `content_hash`
- `published_date` (if available)
- `last_updated` (mandatory in final response if known)
- `retrieval_tags`: expense_ratio, exit_load, riskometer, etc.

## Chunking Strategy

- Chunk size: 500-900 tokens (target ~700)
- Overlap: 80-120 tokens
- Preserve structural boundaries (section headers, bullet lists, tables converted to text)
- Include section title in each chunk to improve retrieval precision

## 5) Ingestion and Indexing Pipeline

1. **Source discovery**
   - Maintain curated source registry per AMC and scheme.
2. **Fetch + parse**
   - Parse HTML into structured text.
   - Keep PDF parser disabled until PDF ingestion is enabled.
3. **Clean + normalize**
   - Remove boilerplate noise while preserving numeric facts and dates.
4. **Chunk + enrich metadata**
   - Add AMC, scheme, section, and date metadata.
5. **Embedding generation**
   - Generate embeddings for semantic retrieval.
6. **Dual indexing**
   - Upsert into vector index and BM25/keyword index.
7. **Quality checks**
   - Validate URL reachability, date presence, numeric formatting, duplicate detection.
8. **Versioning**
   - Keep historical versions by `content_hash` and timestamp.

## Scraping Service (URL Ingestion Service)

Purpose: fetch latest data from the approved in-scope URLs and push normalized content to indexing.

### Service Responsibilities

- Read URL list from the source registry (the URLs defined in this document).
- Fetch page HTML with polite crawling controls (timeouts, retries, user-agent, rate limits).
- Extract structured fields (scheme name, NAV-related values if present, expense ratio, dates, section text).
- Normalize content and metadata into the document schema.
- Detect changes using `content_hash` and `last_seen_at`.
- Publish changed/new documents to indexing workers.

### Runtime Design

- Stateless scraping workers behind a queue.
- One job per URL to isolate failures.
- Retry policy: exponential backoff (for example, 3 attempts).
- Failure handling:
  - mark URL status (`success`, `partial`, `failed`)
  - keep previous indexed version if current scrape fails
- Idempotent writes using `source_url + content_hash`.

### Scraping Output Contract

Each scrape job should emit:

- `source_url`
- `fetched_at`
- `http_status`
- `parsed_sections`
- `normalized_documents[]`
- `content_hash`
- `last_updated` (if present on page, otherwise null with reason)
- `ingestion_status`

## Refresh Cadence

- Primary scheduler: run every day at **9:15 AM** (local deployment timezone) to fetch latest data from all in-scope URLs.
- Daily incremental refresh job is executed by this 9:15 AM schedule.
- Weekly full consistency scan
- Immediate re-index trigger on source change detection

### Scheduler Service: GitHub Actions

- Scheduler platform: GitHub Actions workflow (`.github/workflows/daily-ingestion.yml`)
- Trigger: cron at 9:15 AM daily
- Recommended cron: `45 3 * * *` (UTC) to represent 9:15 AM IST
- Add explicit timezone note in docs/README: scheduler is anchored to IST business time.
- Workflow job sequence:
  1. Checkout repository
  2. Setup runtime (Python/Node)
  3. Load active URL registry
  4. Run scraping pipeline against all in-scope URLs
  5. Run chunking + embedding pipeline for changed docs
  6. Upsert into vector + keyword indexes
  7. Publish ingestion report artifact (success/failure counts, stale URLs, parse errors)
- Reliability controls:
  - `concurrency` group to prevent overlapping daily runs
  - `workflow_dispatch` for manual reruns
  - retry step for transient network failures
  - alert on workflow failure (email/Slack/GitHub notification)

## 6) Separate Architecture: Chunking and Embedding Service

This is an independent post-scrape service. It receives normalized documents from scraping and produces retrieval-ready chunks and embeddings.

### Service Boundaries

- **Input**: `normalized_documents[]` from scraping service
- **Output**:
  - `chunks[]` with chunk metadata
  - `embeddings[]` for each chunk
  - indexing payloads for vector and BM25 stores
- **Invocation**:
  - triggered by GitHub Actions daily run
  - can also be triggered manually for backfill/reprocess

### Processing Pipeline

1. **Document gating**
   - Skip unchanged documents using `source_url + content_hash`.
   - Route changed/new documents to chunker.
2. **Canonical text build**
   - Merge extracted sections in deterministic order.
   - Preserve section headers and key numeric fields.
3. **Chunk creation**
   - Token-aware splitting with target size and overlap.
   - Keep semantic boundaries (heading/paragraph/list/table blocks).
4. **Chunk metadata enrichment**
   - Attach provenance and retrieval metadata to every chunk.
5. **Embedding generation**
   - Generate one vector per chunk using a fixed embedding model version.
6. **Validation**
   - Verify chunk coverage, vector dimension, null checks, and metadata completeness.
7. **Index upsert**
   - Upsert chunks+vectors to vector index.
   - Upsert chunk text and metadata to BM25 index.
8. **Audit logging**
   - Persist per-document processing report and failures.

### Chunking Configuration (recommended baseline)

- Strategy: recursive/token-aware semantic chunking
- Target chunk size: 700 tokens
- Minimum chunk size: 300 tokens
- Maximum chunk size: 900 tokens
- Overlap: 100 tokens
- Header carry-forward: include `section_title` prefix in each chunk
- Table handling: convert tables to normalized key-value text before chunking
- Deduplication: drop near-identical chunks using content fingerprint similarity threshold

### Chunk Schema

Each chunk record should include:

- `chunk_id` (stable deterministic ID)
- `doc_id`
- `source_url`
- `source_type`
- `amc_name`
- `scheme_name`
- `section_title`
- `chunk_text`
- `chunk_index`
- `token_count`
- `content_hash`
- `last_updated`
- `embedding_model_version`
- `pipeline_run_id`

### Embedding Configuration

- One embedding per chunk text (`chunk_text`)
- Use a pinned embedding model version (do not auto-upgrade silently)
- Store vector dimension and model info with each chunk
- Batch requests (for example, 32-128 chunks per call) for throughput
- Rate-limit and retry on provider throttling
- Re-embed rules:
  - content changed (`content_hash` changed)
  - embedding model version changed
  - chunking strategy version changed

### Indexing Strategy

- **Vector index payload**:
  - `chunk_id`, embedding vector, compact metadata filters (`scheme_name`, `source_type`, `last_updated`)
- **BM25 index payload**:
  - `chunk_id`, raw chunk text, full metadata for keyword retrieval
- **Atomicity rule**:
  - mark document active only when both vector and BM25 upserts succeed

### Quality Gates (must pass)

- Chunk count > 0 for each changed document
- 100% chunks have non-empty `chunk_text`
- 100% chunks have required metadata (`source_url`, `scheme_name`, `last_updated` or null reason)
- 100% embeddings have expected vector dimension
- Sampling check for factual field retention (expense ratio, dates, exit load where present)

### GitHub Actions Integration for Chunk+Embed

- Suggested workflow stages:
  1. `scrape`
  2. `chunk_embed`
  3. `index_upsert`
  4. `report`
- Pass artifacts between jobs:
  - scraped normalized docs artifact -> chunk/embed job
  - chunk/index summary artifact -> reporting job
- Cache dependencies to reduce runtime.
- Fail workflow if chunk+embed quality gates fail.

## 7) Query Processing and Retrieval Flow

1. **Thread context load**
   - Fetch recent messages by `thread_id` with strict token budget.
2. **Intent classification**
   - `factual_query` vs `advisory_query` vs `out_of_scope`.
3. **Advisory gate**
   - If advisory: return refusal template immediately.
4. **Query rewriting**
   - Convert user query into search-friendly form:
     - Expand scheme aliases
     - Preserve numeric constraints and date terms
5. **Hybrid retrieval**
   - Run semantic vector search + BM25 keyword search in parallel.
6. **Fusion and reranking**
   - Merge candidates and rerank for factual relevance + source quality.
7. **Evidence thresholding**
   - Require minimum confidence and source coverage.
   - If insufficient evidence: abstain with transparent message.

## Retrieval Settings (recommended baseline)

- Top-K vector candidates: 20
- Top-K BM25 candidates: 20
- Reranked final context: 5-8 chunks
- Minimum source diversity: 1-2 authoritative docs
- Confidence threshold: tune via evaluation set

## 8) Answer Generation Contract

The generator must follow a strict response schema:

1. **Answer (facts only)**
2. **Sources**
   - Bullet list of URLs used
3. **Last updated**
   - Date per source or explicit "Not available in source"
4. **Compliance line**
   - "Facts-only. No investment advice."

## Hard Prompt Rules

- Do not infer facts not present in retrieved context.
- Do not provide recommendation, ranking, preference, or forecast.
- If user asks "which is better/best": refuse advisory and optionally offer factual comparison dimensions only.
- If evidence conflicts across sources: show both facts and cite each source.

## 9) Multi-Thread Chat Support

## Thread Model

- `thread_id` uniquely identifies each conversation.
- Context retrieval is scoped by `thread_id`.
- No message leakage across threads.

## Storage Design

- `threads` table: thread metadata, user_id/session_id, timestamps
- `messages` table: role, content, citations, policy_decision, created_at
- Optional message embeddings for semantic memory lookup per thread

## Context Policy

- Use recent N turns (e.g., last 6-10 messages) plus summary memory.
- Store generated answer with citation metadata for auditability.

## Concurrency

- Stateless API workers + shared backing stores
- Idempotency keys on message writes
- Optimistic locking or sequence tokens to preserve message ordering

## 10) Compliance and Safety Layer

## Advisory Query Detector

Rule + classifier hybrid:

- Keyword patterns:
  - "should I invest", "best fund", "recommend", "safe option", "portfolio allocation"
- Semantic classifier:
  - Detect implied advice/prediction intent

## Refusal Template

Example style:

> I can only provide factual information from official mutual fund sources.  
> I cannot provide investment advice or recommendations.  
> Facts-only. No investment advice.

## Output Validator

Before returning response:

- Verify at least 1 valid source URL exists
- Verify at least 1 `last_updated` value exists or explicit unavailable marker
- Verify no advisory phrases in final output
- Block/repair output if validation fails

## 11) Evaluation and Success Metrics

## Offline Evaluation Set

Build benchmark questions grouped by:

- Scheme basics
- Charges (expense ratio, exit load)
- Risk and category
- Eligibility, lock-in, taxation references (factual only)
- Refusal-required advisory prompts

## Metrics

- Retrieval precision@k
- Citation validity rate (URL reachable + relevant)
- Factual accuracy score (human/SME check)
- Advisory refusal accuracy
- Hallucination rate (target near-zero)
- Response completeness (answer + source + date)

## Acceptance Targets (example)

- Citation included: >= 99%
- Advisory refusal correctness: >= 98%
- Factual accuracy: >= 95% on benchmark set
- Hallucination: <= 2%

## 12) Observability and Audit

Log per request:

- `request_id`, `thread_id`, timestamps
- intent classification result
- retrieved chunk IDs and scores
- selected sources and dates
- final policy decision (answer/refuse/abstain)

Dashboards/alerts:

- sudden drop in citation rate
- advisory leakage incidents
- source fetch failures
- stale index warnings

## 13) Deployment Blueprint

## Suggested Components

- API + Orchestrator: FastAPI/Node service
- Vector DB: Pinecone/Weaviate/FAISS/pgvector
- Keyword search: OpenSearch/Elastic/Whoosh equivalent
- Metadata store + chat threads: PostgreSQL
- Queue for ingestion: Celery/RQ/SQS workers
- Object storage for raw documents: S3-compatible bucket

## Environment Separation

- Dev: small source subset + fast iteration
- Staging: production-like policies and evaluation gates
- Prod: read replicas, autoscaling workers, strict policy checks

## Release Controls

- Block release if evaluation thresholds fail
- Canary rollout with policy incident monitoring

## 14) Known Limitations (Expected)

- Cannot answer beyond indexed and approved source set
- Source freshness depends on ingestion schedule
- Complex PDF tables may lose formatting fidelity
- Regulatory interpretation questions may require explicit "out-of-scope" handling

## 15) Minimal Implementation Roadmap

Phase 1:

- Curate AMC + scheme sources
- Build ingestion + chunking + metadata pipeline
- Implement hybrid retrieval and citation-enforced response template

Phase 2:

- Add advisory detector + refusal validator
- Add thread-safe chat storage and context manager
- Create benchmark dataset and offline evaluation

Phase 3:

- Improve reranking and confidence calibration
- Add observability dashboards and stale-source alerts
- Harden production deployment and release gates

---

This architecture directly supports the problem statement requirements: trustworthy factual responses, transparent source attribution, strict non-advisory behavior, and robust multi-thread conversational handling.
