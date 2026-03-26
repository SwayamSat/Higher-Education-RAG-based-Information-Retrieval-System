from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from collections import deque
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, TOP_K_RETRIEVAL, LLM_MODEL_NAME, LLM_BASE_URL, SCORE_THRESHOLD, BM25_WEIGHT, VECTOR_WEIGHT
import logging
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class RelevanceAgent:
    def __init__(self):
        logger.info("Initializing Relevance Agent...")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
            self.vector_store = Chroma(
                persist_directory=CHROMA_DB_PATH,
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=self.embeddings
            )
            
            self.faiss_retriever = self.vector_store.as_retriever(search_kwargs={"k": TOP_K_RETRIEVAL})
            
            # Fetch all docs to build BM25 index
            docs = self.vector_store.get()
            
            if docs['documents']:
                lc_docs = [Document(page_content=content, metadata=meta) for content, meta in zip(docs['documents'], docs['metadatas'])]
                self.bm25_retriever = BM25Retriever.from_documents(lc_docs)
                self.bm25_retriever.k = TOP_K_RETRIEVAL
                
                logger.info("Hybrid (Chroma + BM25) index loaded successfully.")
                self.index_loaded = True
            else:
                self.index_loaded = False
                logger.warning("Index empty. Waiting for documents to be ingested.")
                
        except Exception as e:
            logger.error(f"Error loading Chroma/BM25 index: {e}")
            self.vector_store = None

    def retrieve(self, query):
        if not self.vector_store:
            return []
        
        logger.info(f"Retrieving relevant documents for: '{query}'")
        
        try:
            if not getattr(self, 'index_loaded', False):
                 docs = self.faiss_retriever.invoke(query)
                 results = []
                 for i, doc in enumerate(docs[:TOP_K_RETRIEVAL]):
                     results.append({
                         "content": doc.page_content,
                         "metadata": doc.metadata,
                         "score": 0.0
                     })
                 return results
            else:
                 # Custom Hybrid Retriever logic
                 bm25_docs = self.bm25_retriever.invoke(query)
                 vector_docs = self.faiss_retriever.invoke(query)
                 
                 def rrf_score(rank: int, k: int = 60) -> float:
                     return 1.0 / (k + rank)
                     
                 doc_scores = {}
                 doc_map = {}
                 
                 for rank, doc in enumerate(vector_docs, 1):
                     content = doc.page_content
                     doc_map[content] = doc
                     doc_scores[content] = doc_scores.get(content, 0.0) + rrf_score(rank) * VECTOR_WEIGHT
                     
                 for rank, doc in enumerate(bm25_docs, 1):
                     content = doc.page_content
                     doc_map[content] = doc
                     doc_scores[content] = doc_scores.get(content, 0.0) + rrf_score(rank) * BM25_WEIGHT
                     
                 sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
                 
                 results = []
                 for content, score in sorted_docs[:TOP_K_RETRIEVAL]:
                     results.append({
                         "content": content,
                         "metadata": doc_map[content].metadata,
                         "score": score
                     })
                     
                 return results
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

class GeneratorAgent:
    def __init__(self):
        logger.info(f"Initializing Generator Agent ({LLM_MODEL_NAME})...")
        self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.1)
        self.memory = deque(maxlen=5) # Custom sliding window window
        
        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "context", "question"],
            template="""You are an expert government scheme assistant. 
Use the following pieces of retrieved context and the chat history to answer the question. 
If the information is not in the context, just say that you don't know based on the provided documents. 
Keep the answer concise, accurate, and structured. 
Cite the source document names if possible.

Chat History:
{chat_history}

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
        
        chat_history = ""
        for human_msg, ai_msg in self.memory:
            chat_history += f"Human: {human_msg}\nAI: {ai_msg}\n\n"
        if not chat_history:
            chat_history = "None"
        
        prompt = self.prompt_template.format(chat_history=chat_history, context=context_str, question=query)
        
        logger.info("Generating answer...")
        try:
            response = self.llm.invoke(prompt)
            # Save context to memory
            self.memory.append((query, response.content))
            return response.content
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {e}"

from models import VerificationResult
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException

class FactCheckAgent:
    def __init__(self):
        logger.info("Initializing Fact-Check Agent...")
        self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.0)
        self.parser = PydanticOutputParser(pydantic_object=VerificationResult)
        
        self.verify_prompt = PromptTemplate(
            input_variables=["context", "question", "answer"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
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

{format_instructions}
"""
        )

    def verify(self, query: str, answer: str, context_docs: list) -> VerificationResult:
        if "not available in the provided official documents" in answer:
             return VerificationResult(status="Verified", reason="System correctly identified missing info.")

        context_str = ""
        for doc in context_docs:
            context_str += f"{doc['content']}\n"
            
        prompt = self.verify_prompt.format(context=context_str, question=query, answer=answer)
        
        logger.info("Verifying answer...")
        try:
            response = self.llm.invoke(prompt)
            result = self.parser.invoke(response)
            return result
        except OutputParserException as e:
            logger.error(f"Failed to parse verification output: {e}")
            return VerificationResult(status="Unverified", reason="Parsing failed")
        except Exception as e:
            logger.error(f"Verification systemic error: {e}")
            return VerificationResult(status="Unverified", reason=f"Verification systemic error: {str(e)}")
