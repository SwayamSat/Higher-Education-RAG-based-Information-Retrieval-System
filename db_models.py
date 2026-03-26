from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    department = Column(String, index=True)
    content_hash = Column(String, unique=True, index=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="uploaded") # uploaded, indexing, indexed, error
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class FeedbackModel(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String, index=True)
    rating = Column(Integer) # 1 = positive, 0/-1 = negative
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
