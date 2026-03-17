from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from config import VECTOR_DB_PATH, EMBEDDING_MODEL_NAME, TOP_K_RETRIEVAL, LLM_MODEL_NAME, LLM_BASE_URL
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

class RelevanceAgent:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Relevance Agent...")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
            self.vector_store = FAISS.load_local(
                VECTOR_DB_PATH, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            print(f"{Fore.GREEN}FAISS index loaded successfully.")
        except Exception as e:
            print(f"{Fore.RED}Error loading FAISS index: {e}")
            self.vector_store = None

    def retrieve(self, query):
        if not self.vector_store:
            return []
        
        print(f"{Fore.YELLOW}Retrieving relevant documents for: '{query}'")
        docs = self.vector_store.similarity_search_with_score(query, k=TOP_K_RETRIEVAL)
        
        # Filter based on score if needed, but for now return all top-k
        # Note: FAISS Score is L2 distance (lower is better)
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
        return results

class GeneratorAgent:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Generator Agent ({LLM_MODEL_NAME})...")
        self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.1)
        
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are an expert government scheme assistant. 
Use the following pieces of retrieved context to answer the question. 
If the information is not in the context, just say that you don't know. 
Keep the answer concise, accurate, and structured. 
Cite the source document names if possible.

Context:
{context}

Question: {question}

Answer:"""
        )

    def generate_answer(self, query, context_docs):
        if not context_docs:
            return "The requested information is not available in the provided official documents."
        
        # Prepare context string
        context_str = ""
        for i, doc in enumerate(context_docs):
            context_str += f"[Source: {doc['metadata']['source']}, Page: {doc['metadata'].get('page', 'N/A')}]\n{doc['content']}\n\n"
        
        prompt = self.prompt_template.format(context=context_str, question=query)
        
        print(f"{Fore.YELLOW}Generating answer...")
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating answer: {e}"

class FactCheckAgent:
    def __init__(self):
        print(f"{Fore.CYAN}Initializing Fact-Check Agent...")
        self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.0)
        
        self.verify_prompt = PromptTemplate(
            input_variables=["context", "question", "answer"],
            template="""You are a strict fact-checker. 
Verify if the generated answer is fully supported by the provided context.
Check for hallucinations, incorrect numbers, or unsupported claims.

Context:
{context}

Question: {question}

Generated Answer: {answer}

Task:
1. Does the answer directly answer the question using ONLY the context?
2. Are there any hallucinations?

Output format:
Status: [Verified/Unverified]
Reason: [Explanation]
"""
        )

    def verify(self, query, answer, context_docs):
        if "not available in the provided official documents" in answer:
            return {"status": "Verified", "reason": "System correctly identified missing info."}

        context_str = ""
        for doc in context_docs:
            context_str += f"{doc['content']}\n"
            
        prompt = self.verify_prompt.format(context=context_str, question=query, answer=answer)
        
        print(f"{Fore.YELLOW}Verifying answer...")
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            
            # Simple parsing
            if "Status: Verified" in content or "Status: [Verified]" in content:
                return {"status": "Verified", "reason": content}
            else:
                return {"status": "Unverified", "reason": content}
        except Exception as e:
            return {"status": "Error", "reason": str(e)}
