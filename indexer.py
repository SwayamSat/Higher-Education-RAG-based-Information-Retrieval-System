import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config import DATA_DIR, VECTOR_DB_PATH, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def load_documents():
    """
    Load PDFs from the data directory.
    Returns a list of LangChain Document objects.
    """
    documents = []
    print(f"{Fore.CYAN}Scanning for PDFs in {DATA_DIR}...")
    
    # Recursive search for PDFs
    pdf_files = glob.glob(os.path.join(DATA_DIR, "**", "*.pdf"), recursive=True)
    
    if not pdf_files:
        print(f"{Fore.YELLOW}No PDF files found in {DATA_DIR}")
        return []

    print(f"{Fore.GREEN}Found {len(pdf_files)} PDF files.")
    
    for pdf_path in pdf_files:
        try:
            print(f"Loading: {os.path.basename(pdf_path)}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            # Add metadata for source department (folder name)
            department = os.path.basename(os.path.dirname(pdf_path))
            for doc in docs:
                doc.metadata['department'] = department
                doc.metadata['source'] = os.path.basename(pdf_path)
            
            documents.extend(docs)
        except Exception as e:
            print(f"{Fore.RED}Error loading {pdf_path}: {e}")
            
    return documents

def create_index():
    """
    Load documents, chunk them, create embeddings, and save the FAISS index.
    """
    # 1. Load Documents
    raw_documents = load_documents()
    if not raw_documents:
        print(f"{Fore.RED}No documents to process. Exiting.")
        return

    print(f"{Fore.CYAN}Loaded {len(raw_documents)} pages from PDFs.")

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(raw_documents)
    print(f"{Fore.GREEN}Split documents into {len(chunks)} chunks.")

    # 3. generate Embeddings and Build Index
    print(f"{Fore.CYAN}Generating embeddings using {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    print(f"{Fore.CYAN}Building FAISS index... (this may take a while)")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # 4. Save Index
    print(f"{Fore.CYAN}Saving index to {VECTOR_DB_PATH}...")
    vector_store.save_local(VECTOR_DB_PATH)
    print(f"{Fore.GREEN}Index saved successfully!")

if __name__ == "__main__":
    create_index()
