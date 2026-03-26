import json
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import time
from database import init_db, get_db
from db_models import FeedbackModel, DocumentModel
from typing import Optional
import os

from models import QueryRequest, QueryResponse, SourceDocument, VerificationResult, PipelineStep
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

analytics_data = {
    "total_queries": 0,
    "total_latency_retrieval": 0.0,
    "total_latency_generation": 0.0,
    "total_latency_verification": 0.0,
    "total_latency_correction": 0.0,
    "first_pass_verified": 0,
    "final_pass_verified": 0
}

@app.on_event("startup")
async def startup_event():
    global pipeline
    logger.info("Initializing SQLite database...")
    init_db()
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
        initial_answer = pipeline.generator.generate_answer(req.query, relevant_docs, query_id=query_id)
        latency_ms['generation'] = round((time.time() - t1) * 1000, 2)
        answer = initial_answer

        # Step 3: Verification
        t2 = time.time()
        verification_result = pipeline.verifier.verify(req.query, answer, relevant_docs, query_id=query_id)
        latency_ms['verification'] = round((time.time() - t2) * 1000, 2)
        
        analytics_data["total_queries"] += 1
        analytics_data["total_latency_retrieval"] += latency_ms.get('retrieval', 0)
        analytics_data["total_latency_generation"] += latency_ms.get('generation', 0)
        analytics_data["total_latency_verification"] += latency_ms.get('verification', 0)
        
        # Step 4: Self-Correction Loop
        if verification_result.status != "Verified":
            logger.warning(f"[{query_id}] Verification failed: {verification_result.reason}. Attempting self-correction using supervisor.")
            t3 = time.time()
            
            correction_res = pipeline.correction_supervisor.run_correction(req.query, answer, relevant_docs)
            answer = correction_res["answer"]
            relevant_docs = correction_res["docs"]
            verification_result = correction_res["verification_result"]
            confidence = correction_res["confidence"]
            latency_ms['correction'] = round((time.time() - t3) * 1000, 2)
            analytics_data["total_latency_correction"] += latency_ms['correction']
            
            if verification_result.status == "Verified":
                analytics_data["final_pass_verified"] += 1
        else:
            confidence = "High"
            analytics_data["first_pass_verified"] += 1
            analytics_data["final_pass_verified"] += 1

        # Format sources
        sources = []
        for doc in relevant_docs:
            sources.append(SourceDocument(
                filename=doc['metadata'].get('source', 'Unknown'),
                department=doc['metadata'].get('department', 'Unknown'),
                page=doc['metadata'].get('page', None),
                relevance_score=round(doc['score'], 3)
            ))
            
        pipeline_steps = []
        pipeline_steps.append(PipelineStep(
            agent="RelevanceAgent",
            duration_ms=latency_ms.get('retrieval', 0.0),
            input_summary=req.query[:50],
            output_summary=f"Found {len(relevant_docs)} documents",
            iteration=1
        ))
        pipeline_steps.append(PipelineStep(
            agent="GeneratorAgent",
            duration_ms=latency_ms.get('generation', 0.0),
            input_summary=f"Docs: {len(relevant_docs)}",
            output_summary=f"Generated {len(initial_answer)} chars",
            iteration=1
        ))
        pipeline_steps.append(PipelineStep(
            agent="FactCheckAgent",
            duration_ms=latency_ms.get('verification', 0.0),
            input_summary=f"Answer: {initial_answer[:30]}...",
            output_summary=verification_result.status,
            iteration=1
        ))

        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            verification=verification_result,
            latency_ms=latency_ms,
            query_id=query_id,
            generated_answer=initial_answer,
            pipeline_steps=pipeline_steps
        )
            
    except Exception as e:
        logger.error(f"[{query_id}] Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    query_id = str(uuid.uuid4())
    logger.info(f"[{query_id}] Received streaming query: {req.query}")
    
    async def event_generator():
        try:
            # Step 1: Retrieval
            relevant_docs = pipeline.retriever.retrieve(req.query)
            if not relevant_docs:
                yield f"event: error\ndata: {json.dumps({'message': 'No documents found'})}\n\n"
                return
                
            sources = []
            for doc in relevant_docs:
                sources.append({
                    "filename": doc['metadata'].get('source', 'Unknown'),
                    "department": doc['metadata'].get('department', 'Unknown'),
                    "page": doc['metadata'].get('page', None),
                    "relevance_score": round(doc['score'], 3)
                })
            yield f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n"
            
            # Step 2: Generation Stream
            full_answer = ""
            for chunk in pipeline.generator.stream_answer(req.query, relevant_docs):
                if chunk:
                    full_answer += chunk
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
            
            # Step 3: Verification
            yield f"event: verification\ndata: {json.dumps({'status': 'Verifying...', 'reason': 'Checking against sources'})}\n\n"
            verification_result = pipeline.verifier.verify(req.query, full_answer, relevant_docs)            
            yield f"event: verification\ndata: {json.dumps({'status': verification_result.status, 'reason': verification_result.reason})}\n\n"
            
            # Send steps
            steps = [{
                "agent": "Streamed Pipeline",
                "duration_ms": 0.0,
                "input_summary": req.query[:50],
                "output_summary": verification_result.status,
                "iteration": 1
            }]
            yield f"event: steps\ndata: {json.dumps({'steps': steps})}\n\n"
            
            yield "event: done\ndata: {}\n\n"
            
        except Exception as e:
            logger.error(f"[{query_id}] Stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Work 2.4 Endpoints ---
class FeedbackRequest(BaseModel):
    query_id: str
    rating: int
    comment: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    feedback_entry = FeedbackModel(
        query_id=req.query_id,
        rating=req.rating,
        comment=req.comment
    )
    db.add(feedback_entry)
    db.commit()
    return {"status": "success"}

@app.get("/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    total = db.query(FeedbackModel).count()
    if total == 0:
        return {"total": 0, "positive_percentage": 0.0}
    
    positive_count = db.query(FeedbackModel).filter(FeedbackModel.rating == 1).count()
    return {
        "total": total,
        "positive_percentage": round((positive_count / total) * 100, 2)
    }

@app.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    total = analytics_data["total_queries"]
    if total == 0:
        return {"message": "No queries processed yet"}
        
    avg_latencies = {
        "retrieval_ms": round(analytics_data["total_latency_retrieval"] / total, 2),
        "generation_ms": round(analytics_data["total_latency_generation"] / total, 2),
        "verification_ms": round(analytics_data["total_latency_verification"] / total, 2),
        "correction_ms": round(analytics_data["total_latency_correction"] / total, 2)
    }
    
    first_pass_rate = round((analytics_data["first_pass_verified"] / total) * 100, 2)
    final_pass_rate = round((analytics_data["final_pass_verified"] / total) * 100, 2)
    
    feedback_total = db.query(FeedbackModel).count()
    positive_percentage = 0.0
    if feedback_total > 0:
        positive_count = db.query(FeedbackModel).filter(FeedbackModel.rating == 1).count()
        positive_percentage = round((positive_count / feedback_total) * 100, 2)
        
    return {
        "total_queries": total,
        "average_latencies": avg_latencies,
        "verification_rates": {
            "first_pass_verified_percentage": first_pass_rate,
            "final_verified_percentage": final_pass_rate
        },
        "feedback_summary": {
            "total_feedback": feedback_total,
            "positive_percentage": positive_percentage,
            "negative_percentage": round(100 - positive_percentage, 2) if feedback_total > 0 else 0.0
        }
    }

# --- Work 2.3 Endpoints ---
from document_manager import save_uploaded_file, index_single_document_bg, list_documents, delete_document
from indexer import create_index

@app.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    department: str = Form("General"), 
    db: Session = Depends(get_db)
):
    doc_id = save_uploaded_file(file, department, db)
    file_path = os.path.join("dataset", department, file.filename)
    
    background_tasks.add_task(index_single_document_bg, doc_id, file_path)
    return {"status": "success", "doc_id": doc_id, "message": "File uploaded and indexing started."}

@app.get("/documents")
async def get_documents(db: Session = Depends(get_db)):
    return list_documents(db)

@app.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, db: Session = Depends(get_db)):
    success = delete_document(doc_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "message": "Document deleted."}

@app.post("/documents/reindex")
async def trigger_reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(create_index)
    return {"status": "success", "message": "Full re-index started in background."}
