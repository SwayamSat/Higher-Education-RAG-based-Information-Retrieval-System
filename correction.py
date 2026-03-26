import logging
from agents import GeneratorAgent, RelevanceAgent, FactCheckAgent, call_llm_with_retry
from config import TOP_K_RETRIEVAL

logger = logging.getLogger(__name__)

class CorrectionSupervisor:
    def __init__(self, generator: GeneratorAgent, retriever: RelevanceAgent, verifier: FactCheckAgent):
        self.generator = generator
        self.retriever = retriever
        self.verifier = verifier

    def rewrite_query(self, query: str) -> str:
        prompt = f"Rewrite this query to be more specific for a government document search engine. Output ONLY the new query string without any other text. Original: '{query}'"
        try:
            return call_llm_with_retry(self.generator.llm, prompt).content.strip()
        except Exception as e:
            logger.error(f"Failed to rewrite query: {e}")
            return query

    def run_correction(self, query: str, initial_answer: str, initial_docs: list) -> dict:
        attempts = 0
        strategies_used = []
        answer = initial_answer
        docs = initial_docs
        status = "Unverified"
        verification_result = None

        strategies = [
            ("Expand Retrieval", self._strategy_expand_retrieval),
            ("Query Rewriting", self._strategy_query_rewriting),
            ("Strict Mode", self._strategy_strict_mode)
        ]

        for name, strategy_fn in strategies:
            if attempts >= 3:
                break
            
            logger.info(f"Correction Attempt {attempts + 1}: {name}")
            attempts += 1
            strategies_used.append(name)
            
            try:
                answer, docs = strategy_fn(query)
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
                continue
            
            verification_result = self.verifier.verify(query, answer, docs)
            if verification_result.status == "Verified":
                status = "Verified"
                break
                
        confidence = "Medium" if status == "Verified" else "Low"

        return {
            "answer": answer,
            "docs": docs,
            "correction_attempts": attempts,
            "strategies_used": strategies_used,
            "final_status": status,
            "verification_result": verification_result,
            "confidence": confidence
        }

    def _strategy_expand_retrieval(self, query: str):
        docs = self.retriever.retrieve(query, top_k=TOP_K_RETRIEVAL + 5)
        answer = self.generator.generate_answer(query, docs)
        return answer, docs

    def _strategy_query_rewriting(self, query: str):
        rewritten = self.rewrite_query(query)
        logger.info(f"Rewritten Query: {rewritten}")
        docs = self.retriever.retrieve(rewritten)
        answer = self.generator.generate_answer(rewritten, docs)
        return answer, docs

    def _strategy_strict_mode(self, query: str):
        docs = self.retriever.retrieve(query)
        orig_temp = self.generator.llm.temperature
        self.generator.llm.temperature = 0.0
        
        try:
            strict_query = "Answer using ONLY the following context: " + query
            answer = self.generator.generate_answer(strict_query, docs)
        finally:
            self.generator.llm.temperature = orig_temp
            
        return answer, docs
