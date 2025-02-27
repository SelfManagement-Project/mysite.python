# db/repositories/document_repository.py
from sqlalchemy.orm import Session
from db.connection.database import Base, Documents

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_all(self):
        return self.db.query(Documents).all()
        
    def get_by_id(self, id: int):
        return self.db.query(Documents).filter(Documents.id == id).first()
        
    def create(self, content: str, doc_metadata: str = None):
        # documents 테이블의 실제 컬럼명 확인 필요
        # 예시: 'content'와 'doc_metadata'가 실제 컬럼명이라고 가정
        db_item = Documents(content=content, doc_metadata=doc_metadata)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item