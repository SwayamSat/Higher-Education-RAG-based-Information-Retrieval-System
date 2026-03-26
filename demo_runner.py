import json
import logging
import time
import requests
from config import LLM_BASE_URL
from main import RAGPipeline

logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger("demo")

def pre_warm_ollama():
    logger.info("Pre-warming Ollama model...")
    try:
        from langchain_ollama import ChatOllama
        from config import LLM_MODEL_NAME
        llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.0)
        llm.invoke("Hi")
        logger.info("Model pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Failed to pre-warm model: {e}")

def run_demo():
    print("="*50)
    print("  Smart Education RAG System — Demo Runner")
    print("="*50)
    
    pre_warm_ollama()
    
    logger.info("Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    
    with open("demo/sample_queries.json", "r") as f:
        queries = json.load(f)
        
    logger.info(f"Loaded {len(queries)} sample queries.")
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: {query}")
        print("-" * 40)
        
        t0 = time.time()
        try:
            response = pipeline.process_query(query)
            latency = time.time() - t0
            print(response.strip())
            print(f"\n[Latency: {latency:.2f}s]")
        except Exception as e:
            print(f"Error processing query: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    run_demo()
