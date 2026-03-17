import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "faiss_index")

# Model Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "llama3.2"  # Ollama model name
LLM_BASE_URL = "http://localhost:11434"

# Retrieval Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5
