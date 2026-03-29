from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from collections import deque
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, TOP_K_RETRIEVAL, LLM_MODEL_NAME, LLM_BASE_URL, SCORE_THRESHOLD, BM25_WEIGHT, VECTOR_WEIGHT, USE_LANGFUSE, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
import logging
import time
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

logger = logging.getLogger(__name__)

def get_langfuse_callback(query_id: str, agent_name: str, iteration: int = 1):
    if not USE_LANGFUSE:
        return None
    try:
        from langfuse.callback import CallbackHandler
        return CallbackHandler(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
            tags=[agent_name],
            session_id=query_id,
            metadata={"iteration": iteration}
        )
    except Exception as e:
        logger.warning(f"Failed to load Langfuse callback: {e}")
        return None

def call_llm_with_retry(llm, prompt, max_retries=3, config=None):
    retries = 0
    while retries <= max_retries:
        try:
            if config:
                return llm.invoke(prompt, config=config)
            return llm.invoke(prompt)
        except Exception as e:
            if retries == max_retries:
                logger.error(f"Max retries reached. LLM call failed: {e}")
                raise e
            backoff_time = 2 ** (retries + 1)
            logger.warning(f"LLM call failed with error: {e}. Retrying in {backoff_time}s ({retries + 1}/{max_retries})...")
            time.sleep(backoff_time)
            retries += 1

class RelevanceAgent:
    def __init__(self):
        logger.info("Initializing Relevance Agent...")
        try:
            self.embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL_NAME)
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

    def retrieve(self, query, top_k=None):
        k = top_k or TOP_K_RETRIEVAL
        if not self.vector_store:
            return []
        
        logger.info(f"Retrieving relevant documents for: '{query}'")
        
        try:
            self.faiss_retriever.search_kwargs["k"] = k
            if not getattr(self, 'index_loaded', False):
                 docs = self.faiss_retriever.invoke(query)
                 results = []
                 for i, doc in enumerate(docs[:k]):
                     results.append({
                         "content": doc.page_content,
                         "metadata": doc.metadata,
                         "score": 0.0
                     })
                 return results
            else:
                 # Custom Hybrid Retriever logic
                 self.bm25_retriever.k = k
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
                 for content, score in sorted_docs[:k]:
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

    def generate_answer(self, query, context_docs, query_id="default", iteration=1):
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
            cb = get_langfuse_callback(query_id, "GeneratorAgent", iteration)
            config = {"callbacks": [cb]} if cb else None
            response = call_llm_with_retry(self.llm, prompt, config=config)
            # Save context to memory
            self.memory.append((query, response.content))
            return response.content
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {e}"

    def stream_answer(self, query, context_docs, query_id="default", iteration=1):
        if not context_docs:
            for word in "The requested information is not available in the provided official documents.".split():
                yield word + " "
            return
        
        context_str = ""
        for i, doc in enumerate(context_docs):
            context_str += f"[Source: {doc['metadata'].get('source', 'Unknown')}, Page: {doc['metadata'].get('page', 'N/A')}]\n{doc['content']}\n\n"
        
        chat_history = ""
        for human_msg, ai_msg in self.memory:
            chat_history += f"Human: {human_msg}\nAI: {ai_msg}\n\n"
        if not chat_history:
            chat_history = "None"
        
        prompt = self.prompt_template.format(chat_history=chat_history, context=context_str, question=query)
        
        logger.info("Streaming answer...")
        try:
            cb = get_langfuse_callback(query_id, "GeneratorAgent", iteration)
            config = {"callbacks": [cb]} if cb else None
            full_response = ""
            for chunk in self.llm.stream(prompt, config=config):
                yield chunk.content
                full_response += chunk.content
            self.memory.append((query, full_response))
        except Exception as e:
            logger.error(f"Error streaming answer: {e}")
            yield f"\n[Error: {e}]"

import json as _json
from models import VerificationResult

class FactCheckAgent:
    def __init__(self):
        logger.info("Initializing Fact-Check Agent...")
        # Use native JSON mode — Ollama enforces valid JSON output directly
        self.llm = ChatOllama(model=LLM_MODEL_NAME, base_url=LLM_BASE_URL, temperature=0.0, format="json")
        
        self.verify_prompt = PromptTemplate(
            input_variables=["context", "question", "answer"],
            template="""You are a strict fact-checker for a government education document system.
Verify if the generated answer is fully supported by the provided context.

Context:
{context}

Question: {question}

Generated Answer: {answer}

Respond with a JSON object with exactly two keys:
- "status": one of "Verified", "Unverified", or "Partial"
- "reason": a short one-sentence explanation

Example: {{"status": "Verified", "reason": "The answer is directly supported by the context."}}
"""
        )

    def verify(self, query: str, answer: str, context_docs: list, query_id="default", iteration=1) -> VerificationResult:
        if "not available in the provided official documents" in answer:
            return VerificationResult(status="Verified", reason="System correctly identified missing info.")

        context_str = ""
        for doc in context_docs:
            context_str += f"{doc['content']}\n"

        prompt = self.verify_prompt.format(context=context_str, question=query, answer=answer)

        logger.info("Verifying answer...")
        raw_text = ""
        try:
            cb = get_langfuse_callback(query_id, "FactCheckAgent", iteration)
            config = {"callbacks": [cb]} if cb else None
            response = call_llm_with_retry(self.llm, prompt, config=config)
            raw_text = response.content.strip()

            data = _json.loads(raw_text)
            status = data.get("status", "Unverified")
            reason = data.get("reason", "No reason provided.")

            # Normalise to allowed Literal values
            if status not in ("Verified", "Unverified", "Partial", "Blocked"):
                status = "Unverified"

            return VerificationResult(status=status, reason=reason)

        except _json.JSONDecodeError:
            # Last-resort: extract first {...} block via regex
            import re
            match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
            if match:
                try:
                    data = _json.loads(match.group(0))
                    status = data.get("status", "Unverified")
                    reason = data.get("reason", "Partial parse.")
                    if status not in ("Verified", "Unverified", "Partial", "Blocked"):
                        status = "Unverified"
                    return VerificationResult(status=status, reason=reason)
                except Exception:
                    pass
            logger.error(f"FactCheckAgent JSON decode failed. Raw: {raw_text}")
            return VerificationResult(status="Unverified", reason="Could not parse fact-check response.")

        except Exception as e:
            logger.error(f"Verification systemic error: {e}")
            return VerificationResult(status="Unverified", reason=f"Systemic error: {str(e)}")
