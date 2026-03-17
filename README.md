# Smart Retrieval of Education System (RAG)

An intelligent Retrieval-Augmented Generation (RAG) system designed to provide accurate information about government education schemes in India.

## Features
- **Multi-Source Scraping**: Automatically downloads official scheme documents (PDFs) from MoE, UGC, AICTE, and MSDE.
- **Advanced RAG Pipeline**:
    - **Relevance Agent**: Efficient similarity search using FAISS and HuggingFace embeddings (`all-MiniLM-L6-v2`).
    - **Generator Agent**: Context-aware answer generation using Ollama (`llama3.2`).
    - **Fact-Check Agent**: Automated verification to prevent hallucinations by double-checking answers against retrieved context.
- **Self-Correction**: Simple iterative loop to refine answers if verification fails.
- **CLI Interface**: Interactive command-line interface for querying the system.

## Project Structure
- `agents.py`: Definition of the three AI agents (Relevance, Generator, Fact-Check).
- `main.py`: The main entry point and pipeline orchestrator.
- `indexer.py`: Script to process PDF documents and build the vector database.
- `scrape_documents.py`: Utility to fetch the latest documents from official sources.
- `config.py`: Centralized configuration for models and paths.
- `check_setup.py`: Utility to verify environment and dependencies.

## Prerequisites
- **Python 3.10+**
- **Ollama**: Must be installed and running locally.
    - Download from [ollama.ai](https://ollama.ai/)
    - Pull the required model: `ollama pull llama3.2`

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: If `requirements.txt` is missing, manual install includes: `langchain`, `faiss-cpu`, `sentence-transformers`, `requests`, `beautifulsoup4`, `colorama`, `langchain-huggingface`, `langchain-community`, `pypdf`)*

## Usage
### 1. Scrape Documents
```bash
python scrape_documents.py
```
### 2. Build Index
```bash
python indexer.py
```
### 3. Run the System
```bash
python main.py
```

## Status & Roadmap
- [x] Core RAG Pipeline implementation.
- [x] Multi-agent architecture (Retrieval, Generation, Verification).
- [x] Initial data for AICTE, MoE, and UGC.
- [/] MSDE data scraping fix.
- [ ] Streamlit/React Web UI.
- [ ] Evaluation framework (RAGAS).
