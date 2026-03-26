# Smart RAG-based Information Retrieval System for Higher Education

A self-correcting, multi-agent Retrieval-Augmented Generation (RAG) system specialized in Government Schemes, AICTE norms, and educational policies.

## Features
- **Multi-Agent Pipeline**: Independent Retriever, Generator, and Fact-Checker agents.
- **RRF Hybrid Scoring**: Combines FAISS vector search and BM25 keyword search.
- **Self-Correction**: Supervisors detect hallucinations and retry with dynamic strategies.
- **SSE Streaming API**: Real-time token streaming and verification events.
- **Document Management**: Fast backend indexing and metadata storage with SQLite.

## Quick Start
1. **Install Dependencies**
   ```bash
   pip install -e .
   ```
2. **Start Backend API**
   ```bash
   uvicorn api:app --reload
   ```
3. **Index Documents**
   Upload documents via API or use the CLI interface `python indexer.py`
4. **Run CLI Client** (Optional)
   ```bash
   python main.py
   ```

## API Reference
| Endpoint | Method | Description |
|---|---|---|
| `/query` | POST | Process a normal RAG query |
| `/query/stream` | POST | Process query and stream tokens via SSE |
| `/documents/upload` | POST | Upload and index a new document |
| `/documents` | GET | List all indexed documents |
| `/documents/{doc_id}` | DELETE | Delete document by ID |
| `/documents/reindex` | POST | Trigger global background reindexing |
| `/feedback` | POST | Submit query feedback |
| `/feedback/stats` | GET | Fetch feedback distribution statistics |
| `/analytics` | GET | Get system usage stats and latency metrics |

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flowcharts and multi-agent interactions.
