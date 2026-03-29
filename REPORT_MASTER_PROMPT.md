# MASTER PROMPT — Smart Retrieval of Education System (RAG) — Project Report Generation

---

## INSTRUCTIONS FOR THE AI

You are an experienced academic technical writer. Your job is to produce a **40–45 page** (approximately **12,000–15,000 words**) college / university project report for the project titled **"Smart RAG-based Information Retrieval System for Higher Education — A Self-Correcting Multi-Agent Approach."**

### Writing Style & Tone

- Write in a **natural, human, conversational-yet-academic tone**. Avoid robotic phrasing, mechanical bullet dumps, and overly formal passive voice. Mix active and passive voice naturally.
- Use varied sentence lengths — some short and punchy, some longer and explanatory. Avoid starting every paragraph the same way.
- Include occasional first-person plural ("we designed…", "our approach…", "we observed…") to sound like a real student team wrote it.
- Do **NOT** use clichéd AI phrases such as "in today's digital age", "in the ever-evolving landscape", "it is worth noting that", "leveraging cutting-edge", "delve into", "in conclusion it can be said that". Write like a competent engineering student, not a language model.
- Use concrete, specific language. Instead of "various technologies were used," name them: "we used LangChain 0.3, ChromaDB, and Ollama-hosted Llama 3.2."
- Include minor natural imperfections that a human would write — contractions ("didn't", "we've"), occasional informal transitions ("That said,", "The tricky part was…", "Interestingly,"), and real-world justifications ("We picked ChromaDB over Pinecone because we needed a free, local-first solution that didn't require an API key or cloud subscription.").
- Keep the language anti-AI-detection friendly: avoid repetitive structures, vary paragraph openings, and use domain-specific jargon naturally rather than over-explaining common concepts.

### Hard Rules

1. **Only include technologies, algorithms, architectures, and features that are actually implemented in this project.** Do not add anything speculative or aspirational. Every claim must be traceable to the codebase described below.
2. Do **not** mention FAISS as the primary vector database — the project uses **ChromaDB**. (FAISS is referenced only in legacy code paths and variable names; ChromaDB is the active store.)
3. Do **not** mention Mistral — the project uses **Llama 3.2** via Ollama.
4. Do **not** add authentication, role-based access, user login, or security modules — the project intentionally excludes them for academic simplicity.
5. Do **not** fabricate benchmark numbers. Use placeholder tables with the column structure shown, and mark values as `[TO BE FILLED AFTER TESTING]`.
6. All diagrams should be described textually (for the reader to draw) or rendered as ASCII / Mermaid where appropriate.

---

## PROJECT FACTSHEET (Use This as Ground Truth)

### Project Title
Smart RAG-based Information Retrieval System for Higher Education

### Domain
Government Education Policy Retrieval — specifically AICTE norms, UGC guidelines, Ministry of Education schemes, Skill Development (MSDE) policies, SWAYAM, NPTEL, PM POSHAN, Vidyanjali, DIKSHA, and related program documents.

### Core Approach
Retrieval-Augmented Generation (RAG) with a **Self-Correcting Multi-Agent Pipeline** to minimize hallucination and ensure source-backed, trustworthy answers.

### Tech Stack (Exact)

| Layer | Technology | Version / Details |
|---|---|---|
| Language | Python | ≥ 3.13 |
| LLM Framework | LangChain | 0.3.x (langchain, langchain-core, langchain-community, langchain-experimental, langchain-ollama, langchain-huggingface, langchain-chroma) |
| LLM Hosting | Ollama | Local, default URL `http://localhost:11434` |
| LLM Model | Llama 3.2 | Configurable via `LLM_MODEL_NAME` env var |
| Embedding Model | BAAI/bge-base-en-v1.5 | Via HuggingFaceEmbeddings |
| Vector Database | ChromaDB | Local persistent storage (`chroma_db/` directory) |
| Sparse Retriever | BM25 (rank_bm25) | Via LangChain's `BM25Retriever` |
| Hybrid Scoring | Reciprocal Rank Fusion (RRF) | Custom implementation, BM25 weight = 0.4, Vector weight = 0.6 |
| Backend API | FastAPI | With Uvicorn ASGI server |
| Frontend | Next.js (React + TypeScript) | With SSE streaming integration |
| Database | SQLite | Via SQLAlchemy ORM (documents and feedback tables) |
| Document Parsing | PyPDFLoader, UnstructuredPDFLoader (OCR), Docx2txtLoader, UnstructuredExcelLoader | Supports PDF, DOCX, XLSX |
| Text Splitting | SemanticChunker (primary), RecursiveCharacterTextSplitter (fallback) | Chunk size 1000, overlap 200 |
| Evaluation | RAGAS | Metrics: faithfulness, answer_relevancy, context_precision, context_recall |
| Observability | Langfuse (optional) | Callback-based LLM tracing per agent per iteration |
| Containerization | Docker + Docker Compose | Backend + Frontend services |
| Testing | Pytest + pytest-asyncio | Unit tests with mocking for all three agents, router, and pipeline |
| Data Scraping | BeautifulSoup + Requests | Automated PDF scraping from government websites |
| Data Validation | Pydantic v2 | Structured request/response models |

### Architecture — The Multi-Agent Pipeline

```
User Query
    │
    ▼
[Query Router] ──── direct/clarify ──► Direct Response
    │ (rag)
    ▼
[Relevance Agent] ── Hybrid Retrieval (ChromaDB + BM25 → RRF) ──► Retrieved Docs
    │
    ▼
[Generator Agent] ── LLM-based answer with sliding-window chat memory (5 turns) ──► Generated Answer
    │
    ▼
[Fact-Check Agent] ── Structured verification (Verified / Unverified / Partial / Blocked) ──► Verification Result
    │
    ├── Verified ──► Final Output (Confidence: High)
    │
    └── Unverified ──► [Correction Supervisor] applies up to 3 strategies sequentially:
                            1. Expand Retrieval (TOP_K + 5)
                            2. Query Rewriting (LLM-rephrased query)
                            3. Strict Mode (temperature=0.0, strict system prompt)
                        Each strategy re-generates and re-verifies.
                        If verified → Final Output (Confidence: Medium)
                        If all fail → Final Output (Confidence: Low) with disclaimer
```

### Agent Details

**1. Query Router (`router.py`)**
- Dual-mode: LLM-based classification (rag / direct / clarify / out_of_scope) with keyword-based fallback.
- Caches up to 100 classified queries for performance.
- Fast-path detection for greetings and mathematical expressions.

**2. Relevance Agent (`agents.py` → `RelevanceAgent`)**
- Loads ChromaDB vector store with BAAI/bge-base-en-v1.5 embeddings.
- Builds a parallel BM25 index from all stored documents.
- Hybrid retrieval: runs both retrievers, applies RRF scoring with configurable weights (vector=0.6, BM25=0.4), merges and ranks results.
- Configurable `TOP_K_RETRIEVAL` (default 5), `SCORE_THRESHOLD` (default 1.2).

**3. Generator Agent (`agents.py` → `GeneratorAgent`)**
- Uses ChatOllama (Llama 3.2) with temperature 0.1.
- Custom PromptTemplate with `{chat_history}`, `{context}`, `{question}` variables.
- Sliding-window conversational memory using `collections.deque(maxlen=5)`.
- Supports both synchronous `generate_answer()` and token-level `stream_answer()` for SSE.
- Includes retry logic with exponential backoff (`call_llm_with_retry`, max 3 retries).

**4. Fact-Check Agent (`agents.py` → `FactCheckAgent`)**
- Uses ChatOllama at temperature 0.0 for deterministic checking.
- Outputs structured `VerificationResult` via Pydantic output parser: `{status, reason}`.
- Status values: Verified, Unverified, Partial, Blocked.
- Gracefully handles parsing failures by returning "Unverified."

**5. Correction Supervisor (`correction.py` → `CorrectionSupervisor`)**
- Sequential strategy execution (max 3 attempts):
  - **Strategy 1 — Expand Retrieval**: Re-retrieves with TOP_K + 5.
  - **Strategy 2 — Query Rewriting**: LLM rephrases the query for better semantic overlap.
  - **Strategy 3 — Strict Mode**: Sets temperature to 0.0, prepends strict system instruction, restores temperature after.
- Each strategy regenerates and re-verifies. Stops early on verification success.
- Returns: final answer, docs, attempt count, strategies used, final status, confidence level.

### Document Ingestion Pipeline (`indexer.py`)
- Recursively scans `dataset/` for PDF, DOCX, XLSX files.
- PDF loading: tries UnstructuredPDFLoader (OCR-capable) first, falls back to PyPDFLoader.
- Metadata enrichment: source filename, department (parent folder name), ingestion timestamp, SHA-256 content hash.
- Text splitting: SemanticChunker (percentile breakpoint) preferred, RecursiveCharacterTextSplitter fallback (chunk_size=1000, overlap=200, separators: `\n## `, `\n### `, `\n\n`, `\n`, `. `, ` `).
- Builds ChromaDB index from chunks.

### Document Management (`document_manager.py`)
- Upload via API → saves to `dataset/{department}/` → SHA-256 deduplication → stores metadata in SQLite → triggers background re-indexing.
- CRUD operations: upload, list, delete (with file cleanup).
- Status tracking: uploaded → indexing → indexed / error.

### Data Scraping (`scrape_documents.py`)
- Automated PDF scraping from government websites: MoE, UGC, AICTE, MSDE.
- Uses BeautifulSoup for link extraction, requests for download.
- Polite scraping with 0.5s delays and User-Agent headers.

### API Layer (`api.py`)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/query` | POST | Synchronous RAG query with full pipeline |
| `/query/stream` | POST | SSE streaming — tokens, sources, verification events |
| `/documents/upload` | POST | Upload and background-index a document |
| `/documents` | GET | List all indexed documents |
| `/documents/{doc_id}` | DELETE | Delete a document |
| `/documents/reindex` | POST | Trigger full re-indexing |
| `/feedback` | POST | Submit thumbs-up/down feedback |
| `/feedback/stats` | GET | Feedback distribution |
| `/analytics` | GET | System usage stats, average latencies, verification rates |

- In-memory analytics tracking: total queries, cumulative latencies per stage, first-pass and final-pass verification rates.
- CORS enabled for frontend integration.
- Pipeline steps tracing in response (agent name, duration, input/output summaries).

### Frontend (`frontend/` — Next.js + TypeScript)

**Components:**
- `MessageBubble.tsx` — Renders user/assistant messages with verification badges, source citations, pipeline step visualization.
- `SourceCard.tsx` — Displays retrieved source documents with filename, department, page, relevance score.
- `PipelineStep.tsx` — Visualizes each agent's processing step with timing.
- `Badge.tsx` — Color-coded verification status badges (Verified=green, Unverified=red, Partial=yellow, Blocked=gray).
- `FeedbackButtons.tsx` — Thumbs up/down feedback submission.
- `FileUpload.tsx` — Document upload with department selection.
- `Sidebar.tsx` — Chat session history management.

**Pages:**
- `page.tsx` — Main chat interface with SSE streaming, real-time token rendering.
- `analytics/` — System analytics dashboard.
- `upload/` — Document upload interface.

### Database Schema (`db_models.py`)
- **documents** table: id (PK), filename, department, content_hash (unique), chunk_count, status, uploaded_at.
- **feedback** table: id (PK, auto), query_id, rating (1=positive, 0/-1=negative), comment (nullable), created_at.

### Pydantic Models (`models.py`)
- `QueryRequest`: query, top_k, session_id
- `SourceDocument`: filename, department, page, relevance_score
- `VerificationResult`: status (Verified/Unverified/Partial/Blocked), reason
- `PipelineStep`: agent, duration_ms, input_summary, output_summary, iteration
- `QueryResponse`: answer, sources, confidence (High/Medium/Low), verification, latency_ms, query_id, generated_answer, pipeline_steps

### Input Sanitization (`main.py`)
- Query length limit: 1000 characters.
- Prompt injection guard: blocks queries containing "ignore previous," "system prompt," "forget."

### Evaluation Framework (`evaluation/eval_runner.py`)
- Uses RAGAS library with 4 metrics: faithfulness, answer_relevancy, context_precision, context_recall.
- Runs test dataset through the full pipeline, collects answers and contexts.
- Exports results to JSON with per-query and average metric scores.

### Testing (`tests/`)
- `test_agents.py`: Unit tests for RelevanceAgent.retrieve(), GeneratorAgent.generate_answer(), FactCheckAgent.verify() using mocks.
- `test_pipeline.py`: Integration test for the full RAGPipeline.process_query().
- `test_router.py`: Tests for QueryRouter routing logic.
- `conftest.py`: Shared fixtures (sample_docs, mock_llm_response, mock_verification_result).

### Deployment
- **Dockerfile (Backend)**: Python 3.11-slim, system deps for OCR (poppler-utils, tesseract-ocr, libmagic), pip install from pyproject.toml, runs Uvicorn.
- **Dockerfile (Frontend)**: Next.js build and serve.
- **docker-compose.yml**: Two services (backend on :8000, frontend on :3000), volume mounts for chroma_db and dataset, host.docker.internal for Ollama access.

### Configuration (`config.py`)
- All configurable via environment variables with sensible defaults.
- Key parameters: EMBEDDING_MODEL_NAME, LLM_MODEL_NAME, LLM_BASE_URL, TOP_K_RETRIEVAL (5), SCORE_THRESHOLD (1.2), BM25_WEIGHT (0.4), VECTOR_WEIGHT (0.6), CHUNK_SIZE (1000), CHUNK_OVERLAP (200), USE_SEMANTIC_CHUNKER (True), USE_LLM_ROUTER (True).

---

## REPORT STRUCTURE — Follow This Exactly

Generate the report with the following chapters. Each chapter should flow naturally into the next. Use numbered sections and sub-sections (1.1, 1.2, 2.1, etc.).

---

### Cover Page (1 page)
- Project Title: **Smart RAG-based Information Retrieval System for Higher Education**
- Subtitle: A Self-Correcting Multi-Agent Approach
- Include placeholders: `[Student Name(s)]`, `[Roll Number(s)]`, `[Department]`, `[College Name]`, `[University Name]`, `[Academic Year]`, `[Guide Name & Designation]`

---

### Certificate Page (1 page)
- Standard college certificate template with placeholders for names, signatures, date, and department seal.

---

### Acknowledgement (0.5 page)
- Brief, genuine-sounding acknowledgement thanking guide, department, college, and any open-source communities (LangChain, Ollama, ChromaDB, HuggingFace).

---

### Abstract (1 page)
Government departments manage extensive collections of policies, regulations, and scheme documents. Manually searching through these is slow and depends heavily on individual expertise. This project presents an AI-powered system that lets officials query these documents in plain English and receive accurate, source-backed answers instantly.

The system uses Retrieval-Augmented Generation (RAG), where documents are chunked, embedded using BAAI/bge-base-en-v1.5, and stored in ChromaDB for semantic search. A BM25 sparse index runs alongside for keyword matching, and both are fused using Reciprocal Rank Fusion (RRF).

To tackle the hallucination problem that plagues most RAG systems, the project implements a Self-Correcting Multi-Agent Pipeline consisting of:
- A **Relevance Agent** that performs hybrid retrieval and filters documents.
- A **Generator Agent** that produces answers from validated context.
- A **Fact-Check Agent** that verifies factual accuracy before output.
- A **Correction Supervisor** that applies three sequential fallback strategies (expanded retrieval, query rewriting, strict mode) when verification fails.

The entire system is built with free, open-source tools — Python, LangChain, ChromaDB, Ollama (Llama 3.2), FastAPI, and Next.js — making it cost-effective and deployable without cloud dependencies.

---

### Table of Contents (auto-generated placeholder)

---

### List of Figures (placeholder)

### List of Tables (placeholder)

---

### Chapter 1: Introduction (3–4 pages)

**1.1 Background and Motivation**
- The challenge of information retrieval in government education departments (AICTE, UGC, MoE, MSDE).
- Pain points: thousands of PDF documents, no centralized search, dependence on institutional memory, manual keyword searches that miss context.
- Why existing search tools (basic keyword search, Google) are insufficient for policy documents that need semantic understanding.

**1.2 Problem Statement**
- Formally define the problem: given a natural language query about government education policies, retrieve the most relevant document passages and generate a verified, hallucination-free answer with source citations.

**1.3 Objectives**
1. Build a document ingestion pipeline that processes PDF, DOCX, and XLSX government documents with OCR support.
2. Implement hybrid retrieval combining dense (vector) and sparse (BM25) search with RRF fusion.
3. Design a multi-agent pipeline with independent retrieval, generation, and fact-checking stages.
4. Develop a self-correction mechanism that automatically retries with different strategies when hallucination is detected.
5. Expose the system via a RESTful API with real-time SSE streaming.
6. Build a user-friendly chat-based frontend for officials to interact with.
7. Evaluate the system using established RAG metrics (faithfulness, relevancy, precision, recall).

**1.4 Scope and Limitations**
- Scope: Academic prototype focused on education policy domain documents.
- Limitations: No authentication (intentional for academic simplicity), requires local Ollama setup, dependent on document quality, local LLM performance varies by hardware.

**1.5 Report Organization**
- Brief description of what each chapter covers.

---

### Chapter 2: Literature Review (4–5 pages)

**2.1 Traditional Information Retrieval**
- TF-IDF, BM25, keyword-based search — strengths and limitations for policy documents.
- Why lexical matching fails on paraphrased or context-dependent government queries.

**2.2 Neural / Semantic Search**
- Dense retrieval with embedding models (BERT, Sentence-BERT, BGE family).
- Specifically discuss BAAI/bge-base-en-v1.5 — why it was chosen (strong performance on MTEB benchmarks, open-source, reasonable size for local deployment).
- Vector databases: compare ChromaDB (chosen — local-first, open-source, no API key needed) vs Pinecone (cloud, paid) vs FAISS (no metadata filtering natively) vs Weaviate.

**2.3 Retrieval-Augmented Generation (RAG)**
- The RAG paradigm: retrieve relevant context → augment the LLM prompt → generate grounded answers.
- Key papers: Lewis et al. (2020) RAG paper.
- Why RAG over pure LLM: reduces hallucination, provides source attribution, works with domain-specific knowledge without fine-tuning.

**2.4 Hybrid Retrieval and Reciprocal Rank Fusion**
- Why hybrid (dense + sparse) outperforms either alone.
- RRF algorithm: `score(d) = Σ 1/(k + rank_i)` — explain with the exact formula used in the project (k=60).
- Benefits: no score normalization needed, rank-based, simple and effective.

**2.5 Multi-Agent Systems in NLP**
- Agent-based architectures for complex reasoning tasks.
- The concept of agent specialization — each agent does one thing well (retrieve, generate, verify).
- Self-correction and iterative refinement in LLM pipelines.

**2.6 Hallucination in LLMs**
- Types of hallucination: intrinsic (contradicts source) and extrinsic (unsupported by source).
- Why this is particularly dangerous in government/policy contexts.
- Existing mitigation techniques: grounding, fact-checking, constrained generation.

**2.7 LangChain Framework**
- Overview of LangChain's modular design: chains, prompts, output parsers, retrievers.
- Why LangChain was chosen for this project: wide model support, retriever abstractions, prompt templating.

**2.8 Local LLM Hosting with Ollama**
- Why local LLMs over API-based (GPT, Claude): cost (free), privacy (government data stays local), no internet dependency.
- Ollama's role: easy local model serving, REST API compatible.

---

### Chapter 3: System Design and Architecture (5–6 pages)

**3.1 High-Level System Architecture**
- Draw/describe the full system diagram: User → Next.js Frontend → FastAPI Backend → RAG Pipeline (Router → Relevance Agent → Generator Agent → Fact-Check Agent → Correction Supervisor) → ChromaDB + BM25 + SQLite.
- Include the Mermaid diagram from the Architecture section above.

**3.2 Multi-Agent Pipeline Design**
- Explain why a multi-agent approach was chosen over a monolithic RAG chain.
- Detail each agent's responsibility, inputs, and outputs.
- The handoff protocol between agents.

**3.3 Query Routing**
- The dual-mode router: LLM classification (4 categories: rag, direct, clarify, out_of_scope) with keyword fallback.
- Fast-path detection for greetings and mathematical expressions.
- LRU-style cache (max 100 entries) for repeated queries.

**3.4 Hybrid Retrieval Architecture**
- Dual-index approach: ChromaDB vector index + BM25 sparse index built from the same document chunks.
- RRF fusion implementation details with weights (vector=0.6, BM25=0.4).
- Configurable TOP_K and SCORE_THRESHOLD.

**3.5 Self-Correction Loop Design**
- The three-strategy sequential pipeline: Expand Retrieval → Query Rewriting → Strict Mode.
- Why sequential (not parallel): cost efficiency, early stopping on success.
- Confidence scoring: High (first-pass verified), Medium (corrected and verified), Low (all strategies exhausted).

**3.6 Data Flow Diagram**
- Document ingestion flow: Upload → Save → Hash → Deduplicate → Chunk → Embed → Store in ChromaDB → Update SQLite status.
- Query processing flow: Input → Sanitize → Route → Retrieve → Generate → Verify → (Correct if needed) → Respond.

**3.7 Database Design**
- SQLite schema: documents table (id, filename, department, content_hash, chunk_count, status, uploaded_at) and feedback table (id, query_id, rating, comment, created_at).
- Why SQLite: lightweight, no server needed, perfect for academic prototype.

**3.8 API Design**
- RESTful API with 10 endpoints.
- SSE streaming design for `/query/stream`: event types (sources, token, verification, steps, done, error).
- CORS configuration for frontend-backend communication.

---

### Chapter 4: Implementation (8–10 pages)

This is the most detailed chapter. Walk through the actual code and explain the implementation decisions.

**4.1 Development Environment Setup**
- Python 3.13, `pyproject.toml` with `uv` package manager.
- Ollama installation and model pull (llama3.2).
- Node.js and Next.js for frontend.

**4.2 Configuration Management (`config.py`)**
- Environment variable-driven configuration with `.env` file.
- All key parameters: model names, paths, retrieval settings, weights.
- Why configurable: allows easy experimentation without code changes.

**4.3 Document Ingestion Implementation (`indexer.py`)**
- Recursive file discovery for PDF, DOCX, XLSX.
- Multi-loader strategy: UnstructuredPDFLoader for OCR fallback to PyPDFLoader.
- Metadata enrichment: department from folder structure, SHA-256 hash for deduplication, ingestion timestamp.
- Semantic chunking with percentile breakpoint detection, fallback to recursive character splitting.
- ChromaDB index creation and persistence.

**4.4 Data Scraping (`scrape_documents.py`)**
- Automated PDF collection from MoE, UGC, AICTE, MSDE websites.
- Link extraction using BeautifulSoup (both href and text-based search).
- Polite scraping practices: User-Agent headers, 500ms delays, skip existing files.

**4.5 Relevance Agent Implementation**
- ChromaDB initialization with HuggingFace embeddings.
- BM25 index construction from ChromaDB document store.
- RRF hybrid scoring function: `rrf_score(rank, k=60) = 1.0 / (k + rank)`.
- Weighted fusion: iterate vector results and BM25 results, accumulate RRF scores with respective weights, sort and truncate.
- Graceful degradation: if BM25 index is empty, falls back to vector-only retrieval.

**4.6 Generator Agent Implementation**
- ChatOllama initialization with temperature 0.1.
- Custom prompt template with chat history, context, and question slots.
- Sliding-window memory using `collections.deque(maxlen=5)` — keeps last 5 conversation turns.
- Source citation instruction in the system prompt.
- Token streaming via `.stream()` method for SSE support.
- Exponential backoff retry logic (2^(retry+1) seconds, max 3 retries).

**4.7 Fact-Check Agent Implementation**
- Deterministic verification with temperature 0.0.
- Pydantic output parser for structured `VerificationResult` extraction.
- Verification prompt: checks if answer is supported by context, detects hallucinations and incorrect numbers.
- Graceful handling of parse failures (defaults to "Unverified").
- Special case: auto-verifies "not available" responses.

**4.8 Correction Supervisor Implementation**
- Three-strategy pattern:
  - **Expand Retrieval**: increases TOP_K by 5 to cast a wider net.
  - **Query Rewriting**: uses LLM to rephrase query for better search overlap.
  - **Strict Mode**: temporarily sets temperature to 0.0, prepends "Answer using ONLY the following context:" instruction, restores temperature after.
- Each strategy: retrieve → generate → verify. Stop on first verified result.
- Returns structured result with attempt count, strategies used, final status, and confidence level.

**4.9 Query Router Implementation**
- Keyword list: scheme, policy, scholarship, guidelines, aicte, ugc, ministry, education, yojana, etc.
- Greeting detection for fast direct responses.
- LLM-based classification with PromptTemplate.
- Response validation: checks if LLM output contains a valid category.
- Cache management: clears when size exceeds 100.

**4.10 Pipeline Orchestration (`main.py`)**
- `RAGPipeline` class: initializes all agents and the correction supervisor.
- `process_query()` flow: sanitize → route → retrieve → generate → verify → correct (if needed) → format output.
- Input sanitization: length limit (1000 chars), prompt injection detection.
- Ollama health check on startup.

**4.11 API Layer Implementation (`api.py`)**
- FastAPI app with startup event for pipeline initialization.
- `/query` endpoint: full pipeline with per-stage latency tracking, pipeline step objects.
- `/query/stream` endpoint: SSE generator yielding source, token, verification, and step events.
- Document management endpoints: upload (with background indexing), list, delete, reindex.
- Feedback system: submit and retrieve aggregated stats.
- Analytics endpoint: running averages of latencies, first-pass and final verification rates.

**4.12 Database Layer (`database.py`, `db_models.py`)**
- SQLAlchemy ORM with SQLite backend.
- DocumentModel: tracks uploaded files with content hash for deduplication and status lifecycle.
- FeedbackModel: stores query-level user ratings.
- Dependency injection via FastAPI's `Depends(get_db)`.

**4.13 Document Manager (`document_manager.py`)**
- File upload → save to department folder → SHA-256 deduplication check → SQLite record → background re-indexing.
- Delete: removes both file and database record.

**4.14 Frontend Implementation**
- Next.js with TypeScript and React.
- **Chat Interface** (`page.tsx`): SSE streaming with EventSource, real-time token rendering, message history.
- **MessageBubble Component**: renders messages with verification badges, expandable source cards, and pipeline step visualization.
- **SourceCard Component**: displays retrieved document metadata (filename, department, page, relevance score).
- **Badge Component**: color-coded verification status (green/red/yellow/gray).
- **FeedbackButtons Component**: thumbs up/down per response.
- **FileUpload Component**: drag-and-drop document upload with department selection.
- **Sidebar Component**: chat session history.
- **Analytics Page**: dashboard showing system metrics.
- **Upload Page**: dedicated document management interface.

**4.15 Observability with Langfuse**
- Optional tracing: each LLM call tagged with agent name, session ID, and iteration number.
- Enabled via environment variables (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY).

**4.16 Containerization**
- Backend Dockerfile: Python 3.11-slim with OCR dependencies (poppler-utils, tesseract-ocr).
- Frontend Dockerfile: Next.js build.
- Docker Compose: two-service stack, volume mounts for persistent data, `host.docker.internal` for Ollama access.

---

### Chapter 5: Testing and Evaluation (4–5 pages)

**5.1 Unit Testing**
- Test suite using pytest with mocking.
- `test_agents.py`: Tests for RelevanceAgent retrieval (mock vector store), GeneratorAgent generation (mock LLM), FactCheckAgent verification (mock parser). Describe the mock strategy: patch `__init__`, inject mock dependencies, verify outputs and call counts.
- `test_router.py`: Tests for query classification (greetings → direct, rag keywords → rag, short queries → clarify).
- `test_pipeline.py`: Integration test for full `RAGPipeline.process_query()`.
- `conftest.py`: Shared fixtures — `sample_docs` (list of dicts with content and metadata), `mock_llm_response` (MagicMock with `.content`), `mock_verification_result` (VerificationResult instance).

**5.2 RAGAS Evaluation**
- Evaluation framework using `eval_runner.py` with test dataset (`test_dataset.json`).
- Four metrics explained:
  - **Faithfulness**: Does the answer use only information from the retrieved context?
  - **Answer Relevancy**: Is the answer relevant to the question asked?
  - **Context Precision**: Are the retrieved documents precisely relevant?
  - **Context Recall**: Does the retrieved context cover the ground truth?
- The evaluation pipeline: run queries through full RAG pipeline → collect answers, contexts, ground truths → compute metrics via RAGAS → export to `results.json`.

**5.3 Results**

| Metric | Score |
|---|---|
| Faithfulness | [TO BE FILLED AFTER TESTING] |
| Answer Relevancy | [TO BE FILLED AFTER TESTING] |
| Context Precision | [TO BE FILLED AFTER TESTING] |
| Context Recall | [TO BE FILLED AFTER TESTING] |

**5.4 Self-Correction Effectiveness**

| Metric | Value |
|---|---|
| First-pass verification rate | [TO BE FILLED AFTER TESTING] |
| Final verification rate (after correction) | [TO BE FILLED AFTER TESTING] |
| Average correction attempts | [TO BE FILLED AFTER TESTING] |
| Most effective strategy | [TO BE FILLED AFTER TESTING] |

**5.5 Latency Analysis**

| Pipeline Stage | Average Latency (ms) |
|---|---|
| Retrieval | [TO BE FILLED AFTER TESTING] |
| Generation | [TO BE FILLED AFTER TESTING] |
| Verification | [TO BE FILLED AFTER TESTING] |
| Correction (when triggered) | [TO BE FILLED AFTER TESTING] |
| End-to-End | [TO BE FILLED AFTER TESTING] |

**5.6 Discussion**
- Analyze results: what worked well, where the system struggled.
- Impact of hybrid retrieval vs vector-only.
- Impact of self-correction on answer quality.
- Limitations observed during testing.

---

### Chapter 6: Results and Discussion (3–4 pages)

**6.1 Sample Queries and Outputs**
- Show 3–4 real example queries with:
  - The query text
  - Retrieved sources
  - Generated answer
  - Verification status and reason
  - Whether correction was triggered and which strategies were used
  - Confidence level

**6.2 Comparison: With vs Without Self-Correction**
- Side-by-side comparison showing how the correction loop improved (or maintained) answer quality for specific queries.

**6.3 Hybrid Retrieval vs Single-Mode**
- Discuss how RRF fusion helped cases where keyword-only or vector-only would have missed relevant documents.

**6.4 System Analytics**
- Reference the analytics endpoint output: total queries processed, average latencies, verification rates, feedback distribution.

---

### Chapter 7: Conclusion and Future Work (2–3 pages)

**7.1 Summary of Contributions**
1. A working RAG system tailored for government education policy documents.
2. A novel self-correcting multi-agent pipeline that reduces hallucination.
3. Hybrid retrieval using RRF that outperforms single-mode search.
4. A complete, deployable stack using only free and open-source tools.
5. A real-time SSE streaming interface for responsive interaction.

**7.2 Limitations**
- Local LLM performance depends on hardware (GPU availability).
- Quality depends on input document quality (scanned PDFs may OCR poorly).
- No multi-language support (English only).
- No authentication or multi-tenancy (academic prototype scope).
- Self-correction adds latency when triggered.

**7.3 Future Work**
- **Multi-language support**: Hindi and regional language document processing.
- **Fine-tuned embeddings**: Domain-specific fine-tuning of BGE model on government policy corpus.
- **Advanced chunking**: Table-aware and structure-preserving chunking for policy documents.
- **Cross-document reasoning**: Answer questions that require synthesizing information across multiple documents.
- **User authentication and audit trail**: For production government deployment.
- **Feedback-driven retraining**: Use stored feedback to improve retrieval ranking over time.

---

### References (2–3 pages)
Include properly formatted references (IEEE or APA style) for:
- Lewis et al. (2020) — RAG paper
- Robertson & Zaragoza (2009) — BM25
- Cormack et al. (2009) — Reciprocal Rank Fusion
- BAAI/bge-base-en-v1.5 documentation
- LangChain documentation
- ChromaDB documentation
- Ollama documentation
- RAGAS evaluation framework
- FastAPI documentation
- Next.js documentation
- SQLAlchemy documentation
- Pydantic documentation
- Docker documentation
- Any government education portal references (AICTE, UGC, MoE, MSDE)
- Relevant hallucination detection papers

---

### Appendices

**Appendix A: Configuration Reference**
- Full table of all environment variables with defaults and descriptions.

**Appendix B: API Reference**
- Complete endpoint documentation with request/response schemas.

**Appendix C: Project Directory Structure**
```
Smart-Retrieval-RAG/
├── agents.py           # Multi-agent classes (Relevance, Generator, FactCheck)
├── api.py              # FastAPI REST + SSE endpoints
├── config.py           # Environment-driven configuration
├── correction.py       # CorrectionSupervisor with 3 strategies
├── database.py         # SQLAlchemy engine and session
├── db_models.py        # SQLite table definitions
├── document_manager.py # Upload, dedup, delete logic
├── indexer.py          # Document loading, chunking, indexing
├── main.py             # RAGPipeline orchestrator + CLI
├── models.py           # Pydantic request/response models
├── router.py           # Query classification (LLM + keyword)
├── scrape_documents.py # Government PDF scraper
├── pyproject.toml      # Python dependencies
├── Dockerfile          # Backend container
├── docker-compose.yml  # Multi-service deployment
├── chroma_db/          # Persistent vector index
├── dataset/            # Source documents by department
├── evaluation/
│   ├── eval_runner.py  # RAGAS evaluation script
│   └── test_dataset.json
├── tests/
│   ├── conftest.py     # Shared test fixtures
│   ├── test_agents.py  # Agent unit tests
│   ├── test_pipeline.py# Pipeline integration test
│   └── test_router.py  # Router unit tests
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx        # Main chat interface
    │   │   ├── layout.tsx      # Root layout
    │   │   ├── globals.css     # Global styles
    │   │   ├── analytics/      # Analytics dashboard
    │   │   └── upload/         # Document upload page
    │   └── components/
    │       ├── Badge.tsx
    │       ├── FeedbackButtons.tsx
    │       ├── FileUpload.tsx
    │       ├── MessageBubble.tsx
    │       ├── PipelineStep.tsx
    │       ├── Sidebar.tsx
    │       └── SourceCard.tsx
    ├── package.json
    ├── Dockerfile
    └── tsconfig.json
```

---

## FINAL REMINDERS

1. **Page count target: 40–45 pages.** Each chapter has a page estimate — follow it.
2. **Stay within the project's actual scope.** Do not invent features, technologies, or results.
3. **Write naturally.** Vary sentence structures. Use transitions. Sound like a real student project, not a template.
4. **Use the exact tech names and versions** listed in the factsheet.
5. **Mark all benchmark/metric values as `[TO BE FILLED AFTER TESTING]`** unless real data is provided.
6. **Include diagrams** described textually or in Mermaid format — at least: system architecture, multi-agent pipeline, data flow (ingestion), data flow (query processing), self-correction loop, database ER diagram.
7. **Cite sources** in the references chapter for every technology and algorithm mentioned.
8. Generate the **complete report in Markdown format** with proper heading hierarchy.
