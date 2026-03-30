import os
import shutil
import uuid
import hashlib
from datetime import datetime
import logging
from fastapi import UploadFile
from sqlalchemy.orm import Session
from db_models import DocumentModel
from config import DATA_DIR
from indexer import create_index
from database import SessionLocal

logger = logging.getLogger(__name__)

def save_uploaded_file(file: UploadFile, department: str, db: Session) -> str:
    dep_dir = os.path.join(DATA_DIR, department)
    os.makedirs(dep_dir, exist_ok=True)
    
    file_path = os.path.join(dep_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    doc_id = str(uuid.uuid4())
    
    with open(file_path, "rb") as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
        
    existing_doc = db.query(DocumentModel).filter(DocumentModel.content_hash == content_hash).first()
    if existing_doc:
        os.remove(file_path)
        return existing_doc.id

    db_doc = DocumentModel(
        id=doc_id,
        filename=file.filename,
        department=department,
        content_hash=content_hash,
        status="uploaded"
    )
    db.add(db_doc)
    db.commit()
    return doc_id

def index_single_document_bg(doc_id: str, file_path: str):
    db = SessionLocal()
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if doc:
        doc.status = "indexing"
        db.commit()
    
    try:
        # For simplicity, trigger global re-index which picks up the new file
        create_index()
        
        if doc:
            doc.status = "indexed"
            db.commit()
    except Exception as e:
        logger.error(f"Error indexing document {doc_id}: {e}")
        if doc:
            doc.status = "error"
            db.commit()
    finally:
        db.close()

def list_documents(db: Session):
    return {"items": db.query(DocumentModel).all()}

def delete_document(doc_id: str, db: Session) -> bool:
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        return False
        
    file_path = os.path.join(DATA_DIR, doc.department, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(doc)
    db.commit()
    return True
