import requests
import sys

print("Checking imports...")
try:
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import PromptTemplate
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("Imports Successful.")
except ImportError as e:
    print(f"Import Error: {e}")

print("\nChecking Ollama Connection...")
try:
    response = requests.get("http://localhost:11434/")
    if response.status_code == 200:
        print(f"Ollama is running: {response.text}")
    else:
        print(f"Ollama returned status code: {response.status_code}")
except Exception as e:
    print(f"Count not connect to Ollama: {e}")
    print("Please ensure Ollama is running (e.g., 'ollama serve')")
