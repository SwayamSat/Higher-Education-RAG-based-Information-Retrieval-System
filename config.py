import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Paths
DATA_DIR = os.path.join(BASE_DIR, "dataset")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "faiss_index")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# Model Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3.2")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")

# Retrieval Configuration
USE_SEMANTIC_CHUNKER = os.getenv("USE_SEMANTIC_CHUNKER", "True").lower() in ("true", "1", "t")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "1.2"))
BM25_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6
CHROMA_COLLECTION_NAME = "gov_docs"
