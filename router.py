import re

class QueryRouter:
    def __init__(self):
        self.rag_keywords = [
            "scheme", "policy", "scholarship", "guidelines", "aicte",
            "ugc", "ministry", "education", "fund", "grant", "stipend",
            "pm", "poshan", "vidyanjali", "diksha", "swayam", "nptel", 
            "eligibility", "apply", "document", "criteria", "yojana"
        ]
        
        self.greetings = ["hi", "hello", "hey", "who are you", "what can you do", "help"]
        
    def route(self, query: str) -> str:
        """Routes a query to: 'rag', 'direct', or 'clarify'"""
        query_lower = query.lower()
        
        # 1. Check for exact greetings / help
        if query_lower in self.greetings:
            return "direct"
            
        # 2. Check for RAG relevant keywords
        if any(kw in query_lower for kw in self.rag_keywords):
            return "rag"
            
        # 3. Very short ambiguous queries
        word_count = len(query.split())
        if word_count < 3:
            return "clarify"
            
        # 4. Math, programming or obvious out-of-domain patterns
        # Quick check for math equations (e.g. 2+2, 5*5)
        if re.search(r'^[\d\s\+\-\*\/\(\)\.]+$', query):
             return "direct"
             
        # Default to RAG if unsure, letting the retrieval failure handle it
        return "rag"
