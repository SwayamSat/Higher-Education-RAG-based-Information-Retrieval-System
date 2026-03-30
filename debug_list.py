from database import SessionLocal
from document_manager import list_documents
import json

def test():
    db = SessionLocal()
    try:
        res = list_documents(db)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
