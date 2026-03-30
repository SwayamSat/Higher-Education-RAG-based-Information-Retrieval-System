import os
import glob
import hashlib
import uuid
from database import SessionLocal, init_db
from db_models import DocumentModel
from config import DATA_DIR
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync")

def sync_existing_files():
    init_db()
    db = SessionLocal()
    
    # Recursive search for supported files
    supported_extensions = ["*.pdf", "*.docx", "*.xlsx"]
    files = []
    for ext in supported_extensions:
        files.extend(glob.glob(os.path.join(DATA_DIR, "**", ext), recursive=True))
        
    logger.info(f"Found {len(files)} files in {DATA_DIR}")
    
    added_count = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        department = os.path.basename(os.path.dirname(file_path))
        
        with open(file_path, "rb") as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
            
        existing = db.query(DocumentModel).filter(DocumentModel.content_hash == content_hash).first()
        if not existing:
            doc = DocumentModel(
                id=str(uuid.uuid4()),
                filename=filename,
                department=department,
                content_hash=content_hash,
                status="indexed" # Assume indexed as indexer.py was already run
            )
            db.add(doc)
            added_count += 1
            logger.info(f"Adding to DB: {filename} ({department})")
            
    db.commit()
    db.close()
    logger.info(f"Sync complete. Added {added_count} new entries to SQL database.")

if __name__ == "__main__":
    sync_existing_files()
