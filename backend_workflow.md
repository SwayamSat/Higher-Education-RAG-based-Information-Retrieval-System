# Backend Workflow
## Self-Correcting Multi-Agent RAG — Backend Tasks

> 17 work items across 4 phases. Each task is self-contained and can be done independently within its phase.

---

## Phase 1 — Bug Fixes & Stabilization

### Work 1.1: Fix Duplicate Source Extraction
**File**: [main.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/main.py) (Lines 74-83)
**Problem**: Source extraction runs twice — lines 74-77 and 80-83 are identical code blocks.
**Steps**:
1. Delete lines 74-77 (the first block)
2. Keep lines 80-83 (uses `.get('source', 'Unknown')` which is safer)
3. Run the pipeline to verify output remains the same

**Acceptance**: Only one source extraction block exists; no duplicate sources in responses.

---

### Work 1.2: Fix Deprecated Imports
**File**: [agents.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py)
**Problem**: Using deprecated packages that will break on updates.
**Steps**:
1. Replace `from langchain_community.chat_models import ChatOllama` → `from langchain_ollama import ChatOllama`
2. Replace `from langchain_community.embeddings import HuggingFaceEmbeddings` (L9) → `from langchain_huggingface import HuggingFaceEmbeddings`
3. Ensure `langchain-ollama` and `langchain-huggingface` are in [pyproject.toml](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/pyproject.toml) dependencies
4. Test that all three agents initialize without deprecation warnings

**Acceptance**: No deprecation warnings on startup; all agents work.

---

### Work 1.3: Implement RRF Hybrid Scoring
**File**: [agents.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py) → `RelevanceAgent.retrieve()`
**Problem**: Relevance scores are dummy values (`i * 0.1`).
**Steps**:
1. Implement Reciprocal Rank Fusion function:
   ```python
   def rrf_score(rank: int, k: int = 60) -> float:
       return 1.0 / (k + rank)
   ```
2. Assign BM25 rank-based RRF score to each BM25 result
3. Assign vector rank-based RRF score to each vector result
4. For documents appearing in both, sum their RRF scores
5. Sort merged results by combined RRF score (descending)
6. Return top-K with real RRF scores instead of dummy values
7. Use configured `BM25_WEIGHT` and `VECTOR_WEIGHT` from [config.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/config.py) as multipliers

**Acceptance**: Scores range 0-1, documents appearing in both retrievers rank higher.

---

### Work 1.4: Add Ollama Retry Logic
**File**: [agents.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py) → `GeneratorAgent.generate_answer()` and `FactCheckAgent.verify()`
**Problem**: Single LLM call with no retry — any timeout kills the request.
**Steps**:
1. Create a reusable `call_llm_with_retry(llm, prompt, max_retries=3)` utility function
2. Implement exponential backoff: 2s → 4s → 8s
3. Catch `ConnectionError`, `Timeout`, `HTTPError` exceptions
4. Log each retry attempt
5. Apply to both `GeneratorAgent.generate_answer()` and `FactCheckAgent.verify()`
6. Add a startup health check that pings Ollama before accepting queries

**Acceptance**: System survives a brief Ollama restart; retries are logged.

---

### Work 1.5: Write pytest Test Suite
**Files**: Create `tests/` directory with:
- `tests/__init__.py`
- `tests/test_router.py`
- `tests/test_agents.py`
- `tests/test_pipeline.py`
- `tests/conftest.py`

**Steps**:
1. **`test_router.py`** — Test `QueryRouter.route()`:
   - Greeting → `"direct"`
   - Keyword query → `"rag"`
   - Short ambiguous → `"clarify"`
   - Math expression → `"direct"`
   - Normal sentence → `"rag"` (default)
2. **`test_agents.py`** — Test with mocked Ollama:
   - `RelevanceAgent.retrieve()` returns structured results
   - `GeneratorAgent.generate_answer()` returns string
   - `FactCheckAgent.verify()` returns [VerificationResult](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx#15-19)
3. **`test_pipeline.py`** — Integration test:
   - Full pipeline with mock LLM returns valid [QueryResponse](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/models.py#19-27) structure
4. **`conftest.py`** — Shared fixtures: mock LLM, mock vector store, sample documents
5. Add `pytest` + `pytest-asyncio` to [pyproject.toml](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/pyproject.toml)
6. Verify: `pytest tests/ -v` passes all tests

**Acceptance**: `pytest tests/ -v` → all green, ≥80% agent code coverage.

---

### Work 1.6: Re-enable SemanticChunker
**File**: [indexer.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/indexer.py) (Line 95)
**Problem**: `raise Exception("Disabled SemanticChunker for speed...")` forcefully disables it.
**Steps**:
1. Remove the forced `raise Exception` line
2. Add a config flag `USE_SEMANTIC_CHUNKER = True/False` in [config.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/config.py)
3. Use SemanticChunker when enabled, fall back to `RecursiveCharacterTextSplitter` when disabled or on error
4. Log which chunker was used

**Acceptance**: `USE_SEMANTIC_CHUNKER=true` uses semantic chunking; `false` uses recursive splitting. No forced exceptions.

---

## Phase 2 — Core Enhancements

### Work 2.1: Multi-Strategy Self-Correction Loop
**File**: [main.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/main.py) → `RAGPipeline.process_query()` + new `correction.py`
**Problem**: Current correction is a single naive retry.
**Steps**:
1. Create `correction.py` with a `CorrectionSupervisor` class
2. Implement 3 strategies:
   - **Strategy 1 — Expand Retrieval**: Re-run retrieval with `TOP_K + 5`
   - **Strategy 2 — Query Rewriting**: Use LLM to rephrase the original query, then re-retrieve + re-generate
   - **Strategy 3 — Strict Mode**: Set `temperature=0.0`, prepend "Answer using ONLY the following context:" to prompt
3. Each strategy runs in sequence if the previous verification failed
4. Track which strategies were attempted and their results
5. Return metadata: `correction_attempts: int`, `strategies_used: List[str]`, `final_status: str`
6. Cap at max 3 iterations to prevent infinite loops

**Acceptance**: A query that fails initial verification gets up to 3 correction attempts with different strategies. Metadata tracks the correction journey.

---

### Work 2.2: SSE Streaming Endpoint
**File**: [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py) → new `/query/stream` endpoint
**Steps**:
1. Add `from fastapi.responses import StreamingResponse`
2. Create `POST /query/stream` that:
   - Runs retrieval (non-streamed, instant)
   - Streams generator tokens via `ChatOllama` streaming mode
   - After stream complete, runs verification as a final SSE event
3. SSE event format:
   ```
   event: token
   data: {"text": "partial answer token"}

   event: sources
   data: {"sources": [...]}

   event: verification
   data: {"status": "Verified", "reason": "...", "confidence": "High"}

   event: done
   data: {}
   ```
4. Keep existing `/query` endpoint as non-streaming fallback
5. Add error event type for LLM failures

**Acceptance**: `curl` to `/query/stream` shows token-by-token events followed by sources and verification.

---

### Work 2.3: Document Upload API
**Files**: New `document_manager.py`, modify [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py)
**Steps**:
1. Create `document_manager.py` with:
   - `save_uploaded_file(file, department)` → saves to `dataset/{department}/`
   - `index_single_document(file_path)` → loads, chunks, embeds, adds to ChromaDB
   - `list_documents()` → returns all indexed documents with metadata
   - `delete_document(doc_id)` → removes file + purges vectors from ChromaDB
2. Add API endpoints in [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py):
   - `POST /documents/upload` — accepts `UploadFile` + `department` form field
   - `GET /documents` — list all documents
   - `DELETE /documents/{doc_id}` — delete document
   - `POST /documents/reindex` — trigger full re-index
3. Store document metadata in SQLite (see Work 2.4)
4. Auto-run indexing in background after upload using `BackgroundTasks`

**Acceptance**: Upload a PDF via API → it appears in `/documents` list → queryable within 2 minutes.

---

### Work 2.4: SQLite Database Setup
**Files**: New `database.py`, `db_models.py`
**Steps**:
1. Create `database.py` with SQLAlchemy engine + session setup (SQLite at `./app.db`)
2. Create `db_models.py` with tables:
   - [documents](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/indexer.py#17-77) — filename, department, content_hash, chunk_count, status, uploaded_at
   - `feedback` — query_id, rating, comment, created_at
3. Add startup event in [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py) to create tables on first run
4. Wire document upload/delete to write to [documents](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/indexer.py#17-77) table
5. Add `POST /feedback` endpoint writing to `feedback` table
6. Add `GET /feedback/stats` for basic aggregates (% positive, total count)

**Acceptance**: SQLite file created on startup; documents and feedback persist across restarts.

---

### Work 2.5: Pipeline Step Tracking
**File**: [main.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/main.py), [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py), [models.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/models.py)
**Steps**:
1. Add `PipelineStep` model to [models.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/models.py):
   ```python
   class PipelineStep(BaseModel):
       agent: str
       duration_ms: float
       input_summary: str
       output_summary: str
       iteration: int
   ```
2. Modify `RAGPipeline.process_query()` to collect `PipelineStep` at each stage
3. Add `pipeline_steps: List[PipelineStep]` to [QueryResponse](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/models.py#19-27)
4. Include step data in both `/query` and `/query/stream` responses

**Acceptance**: Response includes `pipeline_steps` array showing each agent's timing and I/O summary.

---

## Phase 3 — Intelligence Upgrades

### Work 3.1: LLM-Based Query Router
**File**: [router.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/router.py) → rewrite [QueryRouter](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/router.py#3-38)
**Steps**:
1. Add an LLM-based classification method using Ollama:
   ```
   Classify this user query into one of: rag, direct, clarify, out_of_scope
   Query: "{query}"
   Output only the category name.
   ```
2. Keep keyword-based routing as a fast fallback
3. Add config flag: `USE_LLM_ROUTER = True/False` in [config.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/config.py)
4. When LLM router is enabled:
   - First check greetings/math with simple rules (fast path)
   - Then use LLM for ambiguous queries
5. Cache recent classifications to avoid re-calling LLM for similar queries

**Acceptance**: "How do I make pasta?" → `out_of_scope`. "Tell me about AICTE" → `rag`. "Hi" → `direct`.

---

### Work 3.2: RAGAS Evaluation Pipeline
**Files**: New `evaluation/` directory:
- `evaluation/__init__.py`
- `evaluation/eval_runner.py`
- `evaluation/test_dataset.json`

**Steps**:
1. Create a curated test dataset of 50+ Q&A pairs:
   - Question, ground truth answer, expected source documents
   - Mix of: factual, comparative, out-of-scope, ambiguous
2. Implement `eval_runner.py` that:
   - Runs each question through the pipeline
   - Calculates RAGAS metrics: **Faithfulness**, **Answer Relevancy**, **Context Precision**, **Context Recall**
   - Outputs a summary report to `evaluation/results.json`
3. Add `ragas` to [pyproject.toml](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/pyproject.toml)
4. Add a `python -m evaluation.eval_runner` entry point

**Acceptance**: Running eval produces a JSON report with 4 RAGAS metrics scored 0-1.

---

### Work 3.3: Langfuse Integration
**File**: [agents.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py), [config.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/config.py)
**Problem**: `langfuse` is already in [pyproject.toml](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/pyproject.toml) but not wired up.
**Steps**:
1. Add Langfuse callback handler to both [GeneratorAgent](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py#89-140) and [FactCheckAgent](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/agents.py#145-194) LLM calls
2. Configure via env vars: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
3. Tag traces with: query_id, agent_name, iteration_number
4. Make it optional — gracefully skip if keys are not set

**Acceptance**: LLM calls appear in Langfuse dashboard with timing and token counts (when configured).

---

## Phase 4 — Polish

### Work 4.1: Analytics Endpoint
**File**: [api.py](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/api.py)
**Steps**:
1. Add `GET /analytics` returning:
   - Total queries processed (from pipeline step logs or a simple counter)
   - Average latency per step
   - Verification pass rate (first-pass and after correction)
   - Feedback summary (% positive, % negative)
2. Query from SQLite tables + in-memory counters

**Acceptance**: `/analytics` returns a JSON object with all stats.

---

### Work 4.2: Update Documentation
**Files**: [README.md](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/README.md), new `ARCHITECTURE.md`
**Steps**:
1. Rewrite [README.md](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/README.md):
   - Updated project description matching PRD
   - Quick start guide (scrape → index → run)
   - API reference table
   - Architecture overview with diagram
2. Create `ARCHITECTURE.md`:
   - Multi-agent pipeline flowchart
   - Self-correction loop explanation
   - Data flow diagram

**Acceptance**: A new developer can set up the project in <10 minutes using only the README.

---

### Work 4.3: Demo Preparation
**Steps**:
1. Create `demo/` folder with:
   - `demo/sample_queries.json` — 15 curated queries showing different system behaviors
   - `demo/sample_documents/` — 3-4 small test PDFs for quick upload demos
2. Create a `demo_runner.py` script that runs through sample queries and prints formatted output
3. Pre-warm Ollama model to avoid cold start during demo
4. Test entire demo flow end-to-end on a clean machine

**Acceptance**: `python demo_runner.py` runs a full demo in < 5 minutes with no errors.
