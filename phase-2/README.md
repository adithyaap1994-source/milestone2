# Phase 2: Compliance + Conversation Intelligence

Implemented scope:

- intent classifier (`factual_query`, `advisory_query`, `out_of_scope`)
- advisory/out-of-scope refusal engine
- strict response validator:
  - source URLs required for factual responses
  - `last_updated` required for factual responses
  - mandatory disclaimer enforcement
- thread-scoped message persistence (`data/threads.json`)
- audit event logging (`data/audit_log.jsonl`) for request/policy/retrieval traceability
- compliance chat orchestration service
- local keyword retrieval path for citations (no cloud dependency)
- API supports concurrent chat sessions with strict `thread_id` isolation

## Run demo

```bash
cd phase-2
pip install -r requirements.txt
python run_phase2_demo.py
```

## Run Phase 2 API

```bash
cd phase-2
python run_phase2_ui.py
```

Phase 2 API runs on `http://localhost:8080`.

## Run dark-theme Next.js frontend

```bash
cd phase-2/frontend
npm install
npm run dev
```

Open `http://localhost:3000` and test:

- factual query path with citations
- advisory/out-of-scope refusal path
- thread isolation by changing `thread_id`

## Run basic static HTML/CSS UI for quick testing

The API server auto-serves this UI from `phase-2/basic-ui` at:

- `http://localhost:8080/`

No separate static server is required.

## Files

- `src/phase2_compliance/policy.py`: intent + refusal + factual response builder
- `src/phase2_compliance/validator.py`: response contract validator
- `src/phase2_compliance/thread_store.py`: thread/message persistence
- `src/phase2_compliance/audit.py`: append-only audit event logger
- `src/phase2_compliance/retrieval_stub.py`: citation retrieval stub using Phase 1 output
- `src/phase2_compliance/chat_service.py`: query-time orchestration
- `run_phase2_demo.py`: sample multi-thread run
- `run_phase2_ui.py`: threaded local API server with CORS and session endpoints
- `frontend/`: dark-theme Next.js testing frontend
- `basic-ui/`: lightweight static HTML/CSS/JS test UI
# Phase 2 (Planned)

Planned implementation scope:

- Advisory query detection and refusal guardrails
- Response output validation (sources + last updated + compliance line)
- Multi-thread chat storage and context management
- Initial benchmark set for factual and refusal evaluation
