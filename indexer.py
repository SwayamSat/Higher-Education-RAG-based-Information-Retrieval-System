import os
import glob
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from config import DATA_DIR, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, USE_SEMANTIC_CHUNKER
import logging
from pathlib import Path
import hashlib
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check once at startup if Unstructured OCR is actually available
_HAS_UNSTRUCTURED_PDF = False
try:
    from unstructured.partition.pdf import partition_pdf  # noqa: F401
    from langchain_community.document_loaders import UnstructuredPDFLoader
    _HAS_UNSTRUCTURED_PDF = True
    logger.info("Unstructured PDF loader is available — OCR-capable loading enabled.")
except ImportError:
    logger.info("Unstructured PDF extras not installed — using PyPDFLoader for all PDFs.")

def load_documents():
    """
    Load PDFs from the data directory.
    Returns a list of LangChain Document objects.
    """
    documents = []
    logger.info(f"Scanning for PDFs in {DATA_DIR}...")
    
    # Recursive search for supported files
    supported_extensions = ["*.pdf", "*.docx", "*.xlsx"]
    files = []
    for ext in supported_extensions:
        files.extend(glob.glob(os.path.join(DATA_DIR, "**", ext), recursive=True))
    
    if not files:
        logger.warning(f"No valid documents found in {DATA_DIR}")
        return []

    logger.info(f"Found {len(files)} document files.")
    
    for file_path in files:
        try:
            logger.info(f"Loading: {os.path.basename(file_path)}")
            ext = Path(file_path).suffix.lower()
            
            if ext == ".pdf":
                if _HAS_UNSTRUCTURED_PDF:
                    try:
                        loader = UnstructuredPDFLoader(file_path, mode="elements")
                        docs = loader.load()
                    except Exception as unstructured_err:
                        logger.warning(f"Unstructured OCR failed ({unstructured_err}), falling back to PyPDFLoader...")
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                else:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            elif ext == ".xlsx":
                loader = UnstructuredExcelLoader(file_path)
                docs = loader.load()
            else:
                continue
                
            department = os.path.basename(os.path.dirname(file_path))
            
            # Read file content for hashing
            with open(file_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()

            for doc in docs:
                doc.metadata['department'] = department
                doc.metadata['source'] = os.path.basename(file_path)
                doc.metadata['ingested_at'] = datetime.utcnow().isoformat()
                doc.metadata['content_hash'] = content_hash
            
            documents.extend(docs)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            
    return documents

def create_index():
    """
    Load documents, chunk them, create embeddings, and save the FAISS index.
    """
    # 1. Load Documents
    raw_documents = load_documents()
    if not raw_documents:
        logger.error("No documents to process. Exiting.")
        return

    logger.info(f"Loaded {len(raw_documents)} pages from PDFs.")

    # 2. Split Text
    logger.info(f"Generating embeddings for semantic chunking using FastEmbed ({EMBEDDING_MODEL_NAME})...")
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    if USE_SEMANTIC_CHUNKER:
        try:
            logger.info("Attempting to use Semantic Chunker...")
            text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
            logger.info("Successfully using Semantic Chunker.")
        except Exception as e:
            logger.warning(f"Semantic chunking failed/unavailable, falling back to basic splitting: {e}")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
            )
            logger.info("Using RecursiveCharacterTextSplitter fallback.")
    else:
        logger.info("Semantic chunker is disabled by config. Using basic splitting.")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
        )
    
    chunks = text_splitter.split_documents(raw_documents)
    logger.info(f"Split documents into {len(chunks)} chunks.")

    # 3. Build Index
    logger.info("Building ChromaDB index... (this may take a while)")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
        collection_name=CHROMA_COLLECTION_NAME
    )
    
    logger.info(f"Index created and persisted to {CHROMA_DB_PATH}")

if __name__ == "__main__":
    create_index()
