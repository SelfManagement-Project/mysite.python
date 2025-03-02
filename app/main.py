from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db.connection.database import engine, Base, get_db
from sqlalchemy import text
from data.preprocessing.chunking import (
    process_all_tables, 
    fetch_data_from_table, 
    extract_text_from_row, 
    split_text_into_chunks
)
from data.embedding.embedding import EmbeddingService
from services.indexing.indexing_service import IndexingService
from vectordb.qdrant_store import QdrantVectorStore
from data.embedding.embedding import EmbeddingService
from cache.query_cache import QueryCache
from postprocessing.threshold.threshold_filter import ThresholdFilter
from services.similarity.search_service import SearchService
from postprocessing.ranking.ranking import RankingProcessor
from llm.models.deepseek_model import DeepSeekLLM
from services.chat.chat_service import ChatService

from api.routes.chat_routes import router as chat_router


# 서비스 초기화
embedding_service = EmbeddingService()
vector_store = QdrantVectorStore()
indexing_service = IndexingService(embedding_service, vector_store)
query_cache = QueryCache()
threshold_filter = ThresholdFilter(threshold=0.1)
ranking_processor = RankingProcessor()  # 랭킹 프로세서 초기화
search_service = SearchService(
    vector_store=vector_store,
    embedding_service=embedding_service,
    threshold_filter=threshold_filter,
    query_cache=query_cache,
    ranking_processor=ranking_processor
)
llm_model = DeepSeekLLM(model_name = "deepseek-ai/deepseek-coder-1.3b-instruct", device="cuda")

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# ✅ CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (보안상 문제 있으면 특정 도메인만 허용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.post("/reset-vectordb")
def reset_vector_database():
    try:
        # 모든 벡터 데이터 삭제
        success = vector_store.delete_all()
        if success:
            return {"status": "success", "message": "모든 벡터 데이터가 삭제되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="벡터 데이터 삭제 실패")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벡터 데이터베이스 초기화 실패: {str(e)}")

@app.post("/index/all")
def index_all_tables(db: Session = Depends(get_db)):
    try:
        result = indexing_service.index_all_tables(db, exclude_tables=["migrations", "alembic_version"])
        return {"status": "success", "message": "All tables indexed successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@app.post("/index/table/{table_name}")
def index_table(table_name: str, db: Session = Depends(get_db)):
    try:
        # 데이터베이스에서 모든 테이블 이름 가져오기
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        allowed_tables = [row[0] for row in result]
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} is not allowed or does not exist")
        
        result = indexing_service.index_table(db, table_name)
        return {"status": "success", "message": f"Table {table_name} indexed successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
    
@app.get("/search")
def search_similar(query: str, top_k: int = 5, use_cache: bool = True, threshold: float = None):
    try:
        # 요청별 임계값 설정 가능 (기본값 사용)
        if threshold is not None:
            threshold_filter.threshold = threshold
        
        # 검색 수행
        result = search_service.search(query, top_k, use_cache)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# 청크분할 된 db데이터 임베딩딩 확인
@app.get("/embeddings/{table_name}")
def get_table_embeddings(table_name: str, limit: int = 5, db: Session = Depends(get_db)):
    try:
        # 데이터베이스에서 모든 테이블 이름 가져오기
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        allowed_tables = [row[0] for row in result]
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} is not allowed or does not exist")
        
        # 1. 특정 테이블의 데이터 가져오기
        rows = fetch_data_from_table(db, table_name, limit=10)  # 테스트를 위해 일부만 가져옴
        
        # 2. 청크 분할
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
        
        # 3. 임베딩 생성
        processed_data = embedding_service.process_chunks(chunked_data)
        
        # 4. 결과의 일부만 반환
        sample_data = processed_data[:limit]
        
        return {
            "status": "success", 
            "table": table_name,
            "total_processed": len(processed_data),
            "sample_data": sample_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding process failed: {str(e)}")

# db데이터 청크분할 확인
@app.get("/chunks")
def get_chunks(limit: int = 5, db: Session = Depends(get_db)):
    try:
        # 청크 분할 처리 실행
        chunked_data = process_all_tables(db, exclude_tables=["migrations", "alembic_version"])
        
        # 결과의 일부만 반환 (전체 데이터가 너무 클 수 있음)
        sample_chunks = chunked_data[:limit]
        
        return {
            "status": "success", 
            "total_chunks": len(chunked_data),
            "sample_chunks": sample_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking process failed: {str(e)}")
    
@app.get("/chunks/{table_name}")
def get_table_chunks(table_name: str, limit: int = 5, db: Session = Depends(get_db)):
    try:
        # 데이터베이스에서 모든 테이블 이름 가져오기
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        allowed_tables = [row[0] for row in result]
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} is not allowed or does not exist")
        
        # 해당 테이블만 처리
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
        
        # 결과의 일부만 반환
        sample_chunks = chunked_data[:limit]
        
        return {
            "status": "success", 
            "table": table_name,
            "total_chunks": len(chunked_data),
            "sample_chunks": sample_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking process failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Hello, Chatbot!"}


# db 연결 확인인
@app.get("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # text() 함수로 SQL 쿼리를 감싸기
        result = db.execute(text("SELECT 1")).fetchone()
        if result:
            return {"status": "success", "message": "Database connection successful!"}
        else:
            return {"status": "error", "message": "Database query did not return expected result"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# db 연결 및 테이블 불러오기 확인
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    try:
        # text() 함수로 SQL 쿼리를 감싸서 user 테이블 조회
        result = db.execute(text("SELECT * FROM \"user\" LIMIT 10")).fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        users = []
        for row in result:
            user_dict = dict(row._mapping)
            users.append(user_dict)
            
        return {"status": "success", "data": users, "count": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    
# db 연결 및 테이블 불러오기 확인
@app.get("/table/{table_name}")
def get_table_data(table_name: str, limit: int = 10, db: Session = Depends(get_db)):
    try:
        # 데이터베이스에서 모든 테이블 이름 가져오기
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        allowed_tables = [row[0] for row in result]
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} is not allowed or does not exist")
        
        # 안전한 쿼리 실행
        result = db.execute(text(f"SELECT * FROM \"{table_name}\" LIMIT :limit"), {"limit": limit}).fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        data = []
        for row in result:
            data.append(dict(row._mapping))
            
        return {"status": "success", "table": table_name, "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


################################################################################################
# 프론트 통신

################################################################################################


################################################################################################
# 백엔드(자바)데이터 동기화 엔드포인트
# 특정 레코드만 인덱싱하는 엔드포인트
@app.post("/index/record/{table_name}/{record_id}")
def index_single_record(table_name: str, record_id: int, db: Session = Depends(get_db)):
    try:
        # 데이터베이스에서 모든 테이블 이름 가져오기
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        allowed_tables = [row[0] for row in result]
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} is not allowed or does not exist")
        
        # 특정 레코드 가져오기
        record = db.execute(text(f"SELECT * FROM \"{table_name}\" WHERE id = :id"), {"id": record_id}).fetchone()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Record with id {record_id} not found in table {table_name}")
        
        # 해당 레코드 처리
        row_text = extract_text_from_row(record)
        chunks = split_text_into_chunks(row_text)
        
        chunked_data = []
        for i, chunk in enumerate(chunks):
            chunked_data.append({
                'text': chunk,
                'metadata': {
                    'table': table_name,
                    'row_id': record_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            })
        
        # 기존 데이터 삭제 (업데이트 경우 필요)
        vector_store.delete_by_metadata(table_name, record_id)
        
        # 임베딩 생성 및 저장
        if chunked_data:
            texts = [item['text'] for item in chunked_data]
            embeddings = embedding_service.generate_embeddings(texts)
            
            metadatas = []
            for j, item in enumerate(chunked_data):
                metadata = item['metadata']
                metadata['text'] = texts[j]
                metadatas.append(metadata)
            
            vector_store.add_embeddings(embeddings, metadatas)
        
        return {
            "status": "success", 
            "message": f"Record {record_id} from table {table_name} indexed successfully",
            "chunks_indexed": len(chunked_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

# 인덱스에서 특정 레코드 삭제하는 엔드포인트
@app.post("/index/delete/{table_name}/{record_id}")
def delete_from_index(table_name: str, record_id: int):
    try:
        # 인덱스에서 해당 레코드 삭제
        vector_store.delete_by_metadata(table_name, record_id)
        
        return {
            "status": "success",
            "message": f"Record {record_id} from table {table_name} was removed from the index"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index deletion failed: {str(e)}")

################################################################################################

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)