from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import uuid
import logging
import os

from models import QueryRequest, QueryResponse, SourceDocument, VerificationResult
from main import RAGPipeline

# Setup basic logging for the API layer
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api")

app = FastAPI(title="Smart Retrieval RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = None

@app.on_event("startup")
async def startup_event():
    global pipeline
    logger.info("Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    logger.info("RAG Pipeline Ready.")

@app.get("/health")
async def health_check():
    return {"status": "ok", "pipeline_initialized": pipeline is not None}

@app.post("/query", response_model=QueryResponse)
async def query_documents(req: QueryRequest):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    query_id = str(uuid.uuid4())
    logger.info(f"[{query_id}] Received query: {req.query}")
    
    # Timing dictionary
    latency_ms = {}
    
    try:
        # Step 1: Retrieval
        t0 = time.time()
        relevant_docs = pipeline.retriever.retrieve(req.query)
        latency_ms['retrieval'] = round((time.time() - t0) * 1000, 2)
        
        if not relevant_docs:
            return QueryResponse(
                answer="The requested information is not available in the provided official documents.",
                sources=[],
                confidence="Low",
                verification=VerificationResult(status="Blocked", reason="No relevant documents found in index."),
                latency_ms=latency_ms,
                query_id=query_id
            )

        # Step 2: Generation
        t1 = time.time()
        initial_answer = pipeline.generator.generate_answer(req.query, relevant_docs)
        latency_ms['generation'] = round((time.time() - t1) * 1000, 2)
        answer = initial_answer

        # Step 3: Verification
        t2 = time.time()
        verification_result = pipeline.verifier.verify(req.query, answer, relevant_docs)
        latency_ms['verification'] = round((time.time() - t2) * 1000, 2)
        
        # Step 4: Simple Self-Correction
        if verification_result.status != "Verified":
            logger.warning(f"[{query_id}] Verification failed: {verification_result.reason}. Attempting self-correction.")
            t3 = time.time()
            new_query = req.query + " (Ensure answer is strictly based on context)"
            answer = pipeline.generator.generate_answer(new_query, relevant_docs)
            
            # Re-verify
            verification_result = pipeline.verifier.verify(new_query, answer, relevant_docs)
            latency_ms['correction'] = round((time.time() - t3) * 1000, 2)
            
            if verification_result.status != "Verified":
                answer = "The requested information could not be verified from official documents."
                confidence = "Low"
            else:
                confidence = "Medium"
        else:
            confidence = "High"

        # Format sources
        sources = []
        for doc in relevant_docs:
            sources.append(SourceDocument(
                filename=doc['metadata'].get('source', 'Unknown'),
                department=doc['metadata'].get('department', 'Unknown'),
                page=doc['metadata'].get('page', None),
                relevance_score=round(doc['score'], 3)
            ))
            
        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            verification=verification_result,
            latency_ms=latency_ms,
            query_id=query_id,
            generated_answer=initial_answer
        )
            
    except Exception as e:
        logger.error(f"[{query_id}] Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
