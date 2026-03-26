import logging
import requests
import sys
from agents import RelevanceAgent, GeneratorAgent, FactCheckAgent
from router import QueryRouter
from config import LLM_BASE_URL
from correction import CorrectionSupervisor

logger = logging.getLogger(__name__)

def ping_ollama():
    try:
        url = LLM_BASE_URL.replace('/api', '')
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        logger.info("Ollama health check passed.")
        return True
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}. Please ensure Ollama is running.")
        return False

def sanitize_query(query: str) -> str:
    query = query.strip()
    if len(query) > 1000:
        raise ValueError("Query exceeds maximum length of 1000 characters.")
    
    forbidden = ["ignore previous", "system prompt", "forget"]
    if any(f in query.lower() for f in forbidden):
        raise ValueError("Invalid query pattern detected. Please rephrase your question.")
    return query

class RAGPipeline:
    def __init__(self):
        self.router = QueryRouter()
        self.retriever = RelevanceAgent()
        self.generator = GeneratorAgent()
        self.verifier = FactCheckAgent()
        self.correction_supervisor = CorrectionSupervisor(self.generator, self.retriever, self.verifier)

    def process_query(self, query):
        try:
            query = sanitize_query(query)
        except ValueError as e:
            return self.format_output(str(e), "N/A", "Low", {"status": "Blocked", "reason": "Sanitization failed"})

        logger.info(f"Processing Query: {query}")

        route = self.router.route(query)
        logger.info(f"Query routed as: {route}")

        if route == "direct":
            return self.format_output("I am the Government Scheme Assistant. I can help you find information on scholarships, AICTE norms, and various government policies via official documents. How can I help you today?", "N/A", "High", {"status": "Verified", "reason": "Direct Answer"})
        elif route == "clarify":
            return self.format_output("Could you provide more details? (e.g., 'What is the PM POSHAN scheme?' or 'AICTE scholarships list')", "N/A", "High", {"status": "Verified", "reason": "Clarification Request"})

        # Step 1: Retrieval
        relevant_docs = self.retriever.retrieve(query)
        if not relevant_docs:
            return self.format_output("The requested information is not available in the provided official documents.", "N/A", "Low", {"status": "N/A", "reason": "No documents found"})

        # Step 2: Generation
        # Step 2: Generation
        initial_answer = self.generator.generate_answer(query, relevant_docs)
        answer = initial_answer

        # Step 3: Verification
        verification_result = self.verifier.verify(query, answer, relevant_docs)
        
        # Step 4: Self-Correction Loop
        metadata = {}
        if verification_result.status != "Verified":
            logger.warning(f"Verification Failed: {verification_result.reason}")
            
            correction_res = self.correction_supervisor.run_correction(query, answer, relevant_docs)
            answer = correction_res["answer"]
            relevant_docs = correction_res["docs"]
            verification_result = correction_res["verification_result"]
            confidence = correction_res["confidence"]
            metadata = {
                "correction_attempts": correction_res["correction_attempts"],
                "strategies_used": correction_res["strategies_used"],
                "final_status": correction_res["final_status"]
            }
        else:
            confidence = "High"

        # Extract Sources
        sources = set()
        for doc in relevant_docs:
            sources.add(doc['metadata'].get('source', 'Unknown'))
        source_str = ", ".join(sources) if sources else "N/A"

        return self.format_output(answer, source_str, confidence, verification_result, generated_answer=initial_answer, metadata=metadata)

    def format_output(self, answer, source, confidence, verification_result=None, generated_answer=None, metadata=None):
        output = f"""
Final Answer:
{answer}
"""
        if generated_answer and generated_answer != answer:
            output += f"""
Generated Answer (Before Verification):
{generated_answer}
"""

        output += f"""
Source:
{source}

Confidence:
{confidence}
"""
        if getattr(verification_result, 'status', None) or (isinstance(verification_result, dict) and verification_result.get('status')):
             v_status = verification_result.status if hasattr(verification_result, 'status') else verification_result['status']
             v_reason = verification_result.reason if hasattr(verification_result, 'reason') else verification_result['reason']
             output += f"""
Verification Status:
{v_status}

Verification Reason:
{v_reason}
"""
        if metadata and metadata.get('correction_attempts'):
            output += f"""
Correction Attempts: {metadata['correction_attempts']}
Strategies Used: {", ".join(metadata['strategies_used'])}
Correction Final Status: {metadata['final_status']}
"""
        return output

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Smart Retrieval of Education Schemes (RAG System)")
    print("Type 'exit' to quit.\n")
    
    if not ping_ollama():
        print("Warning: Ollama is not responding. Ensure the service is running.")
        print("Continuing anyway, but generation might fail.")
    
    pipeline = RAGPipeline()
    
    while True:
        try:
            query = input("\nEnter your query: ")
            if query.lower() in ['exit', 'quit']:
                break
            
            if not query.strip():
                continue
                
            response = pipeline.process_query(query)
            print(response)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
