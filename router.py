import re
import logging
from config import USE_LLM_ROUTER, LLM_MODEL_NAME, LLM_BASE_URL

logger = logging.getLogger(__name__)

class QueryRouter:
    def __init__(self):
        self.rag_keywords = [
            "scheme", "policy", "scholarship", "guidelines", "aicte",
            "ugc", "ministry", "education", "fund", "grant", "stipend",
            "pm", "poshan", "vidyanjali", "diksha", "swayam", "nptel", 
            "eligibility", "apply", "document", "criteria", "yojana"
        ]
        
        self.greetings = ["hi", "hello", "hey", "who are you", "what can you do", "help"]
        self.cache = {}
        
        if USE_LLM_ROUTER:
            try:
                from langchain_ollama import ChatOllama
                from langchain_core.prompts import PromptTemplate
                self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.0)
                self.prompt = PromptTemplate(
                    input_variables=["query"],
                    template="""Classify this user query into one of: rag, direct, clarify, out_of_scope
Query: "{query}"
Output only the category name."""
                )
            except Exception as e:
                logger.error(f"Could not load LLM for router: {e}")
                self.llm = None
        else:
            self.llm = None
            
    def route(self, query: str) -> str:
        """Routes a query to: 'rag', 'direct', 'clarify', or 'out_of_scope'"""
        query_lower = query.lower()
        
        # 1. Cache Check
        if USE_LLM_ROUTER and query_lower in self.cache:
            return self.cache[query_lower]
            
        # 2. Check for exact greetings / help (fast path)
        if query_lower in self.greetings:
            return "direct"
            
        # 3. Math, programming or obvious out-of-domain patterns (fast path)
        if re.search(r'^[\d\s\+\-\*\/\(\)\.]+$', query):
             return "direct"
             
        # 4. LLM Routing
        if USE_LLM_ROUTER and self.llm:
            try:
                prompt_text = self.prompt.format(query=query)
                response = self.llm.invoke(prompt_text).content.strip().lower()
                
                # Verify and cache
                for cat in ["rag", "direct", "clarify", "out_of_scope"]:
                    if cat in response:
                        if len(self.cache) > 100:
                            self.cache.clear()
                        self.cache[query_lower] = cat
                        return cat
                        
                self.cache[query_lower] = "rag"
                return "rag"
            except Exception as e:
                logger.error(f"LLM routing failed: {e}. Falling back to keywords.")
                
        # 5. Fallbacks if LLM is disabled or fails
        if any(kw in query_lower for kw in self.rag_keywords):
            return "rag"
            
        word_count = len(query.split())
        if word_count < 3:
            return "clarify"
            
        return "rag"
