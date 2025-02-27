# services/indexing/indexing_service.py
from data.preprocessing.chunking import process_all_tables, fetch_data_from_table, extract_text_from_row, split_text_into_chunks
from data.embedding.embedding import EmbeddingService
from vectordb.qdrant_store import QdrantVectorStore
from sqlalchemy.orm import Session
from sqlalchemy import text

class IndexingService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: QdrantVectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def index_all_tables(self, db: Session, exclude_tables=None, batch_size: int = 100):
        """모든 테이블 데이터 인덱싱"""
        # 데이터 청크 분할
        chunked_data = process_all_tables(db, exclude_tables, chunk_size=1000)
        
        # 배치 처리 (메모리 관리)
        total_indexed = 0
        for i in range(0, len(chunked_data), batch_size):
            batch = chunked_data[i:i+batch_size]
            
            # 임베딩 생성
            texts = [item['text'] for item in batch]
            embeddings = self.embedding_service.generate_embeddings(texts)
            
            # 메타데이터 추출 (텍스트도 포함)
            metadatas = []
            for j, item in enumerate(batch):
                metadata = item['metadata']
                metadata['text'] = texts[j]  # 원본 텍스트도 메타데이터에 저장
                metadatas.append(metadata)
            
            # 임베딩 및 메타데이터 저장
            result = self.vector_store.add_embeddings(embeddings, metadatas)
            total_indexed += result["inserted"]
            
            print(f"Indexed batch {i//batch_size + 1}, total vectors so far: {total_indexed}")
        
        return {"total_indexed": total_indexed, "total_vectors": self.vector_store.count()}
    
    def index_table(self, db: Session, table_name: str, batch_size: int = 100):
        """특정 테이블만 인덱싱"""
        rows = fetch_data_from_table(db, table_name)
        chunked_data = []
        
        for row_index, row in enumerate(rows):
            row_text = extract_text_from_row(row)
            row_id = row._mapping.get('id', row_index)
            chunks = split_text_into_chunks(row_text)
            
            for i, chunk in enumerate(chunks):
                chunked_data.append({
                    'text': chunk,
                    'metadata': {
                        'table': table_name,
                        'row_id': row_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })
        
        # 배치 처리
        total_indexed = 0
        for i in range(0, len(chunked_data), batch_size):
            batch = chunked_data[i:i+batch_size]
            
            # 임베딩 생성
            texts = [item['text'] for item in batch]
            embeddings = self.embedding_service.generate_embeddings(texts)
            
            # 메타데이터 추출 (텍스트도 포함)
            metadatas = []
            for j, item in enumerate(batch):
                metadata = item['metadata']
                metadata['text'] = texts[j]
                metadatas.append(metadata)
            
            # 임베딩 및 메타데이터 저장
            result = self.vector_store.add_embeddings(embeddings, metadatas)
            total_indexed += result["inserted"]
            
            print(f"Indexed batch {i//batch_size + 1} for table {table_name}, total vectors: {total_indexed}")
        
        return {"table": table_name, "total_indexed": total_indexed}