import os
import glob
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, Docx2txtLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import DATA_DIR, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP
import logging
from pathlib import Path
import hashlib
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
                # Use Unstructured for OCR support on scanned PDFs
                try:
                    loader = UnstructuredPDFLoader(file_path, mode="elements")
                    docs = loader.load()
                except Exception as unstructured_err:
                    logger.warning(f"Unstructured OCR failed ({unstructured_err}), falling back to PyPDFLoader...")
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
    logger.info(f"Generating embeddings for semantic chunking using {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    try:
        raise Exception("Disabled SemanticChunker for speed. Falling back.")
        text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
        logger.info("Using Semantic Chunker to preserve paragraph meaning.")
    except Exception as e:
        logger.warning(f"Semantic chunking failed/unavailable, falling back to basic splitting: {e}")
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
