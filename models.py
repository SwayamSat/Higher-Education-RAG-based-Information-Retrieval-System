from pydantic import BaseModel
from typing import Literal, Optional, List, Dict

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    session_id: Optional[str] = None

class SourceDocument(BaseModel):
    filename: str
    department: str
    page: Optional[int] = None
    relevance_score: float

class VerificationResult(BaseModel):
    status: Literal["Verified", "Unverified", "Partial", "Blocked"]
    reason: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    confidence: Literal["High", "Medium", "Low"]
    verification: VerificationResult
    latency_ms: Dict[str, float]
    query_id: str
    generated_answer: Optional[str] = None # Added for tracing/debugging
