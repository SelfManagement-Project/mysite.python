# data/preprocessing/chunking.py
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any

def get_all_tables(db: Session):
    """데이터베이스의 모든 테이블 이름 가져오기"""
    inspector = inspect(db.bind)
    return inspector.get_table_names()

def fetch_data_from_table(db: Session, table_name: str, limit: int = None):
    """특정 테이블에서 데이터 가져오기"""
    query = f'SELECT * FROM "{table_name}"' + (f" LIMIT {limit}" if limit else "")
    result = db.execute(text(query))
    return result.fetchall()

def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """텍스트를 청크로 분할"""
    chunks = []
    if len(text) <= chunk_size:
        chunks.append(text)
    else:
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk:
                chunks.append(chunk)
    return chunks

def extract_text_from_row(row):
    """행에서 텍스트 데이터 추출"""
    # 모든 컬럼의 값을 문자열로 변환하여 결합
    text_content = []
    for key, value in row._mapping.items():
        if value is not None:
            text_content.append(f"{key}: {value}")
    return " | ".join(text_content)

def process_all_tables(db: Session, exclude_tables=None, chunk_size: int = 1000, chunk_overlap: int = 200):
    """모든 테이블의 데이터 처리 및 청크 분할"""
    if exclude_tables is None:
        exclude_tables = []
    
    tables = get_all_tables(db)
    chunked_data = []
    
    for table in tables:
        if table in exclude_tables:
            continue
            
        print(f"Processing table: {table}")
        rows = fetch_data_from_table(db, table)
        
        for row_index, row in enumerate(rows):
            # 행에서 텍스트 추출
            row_text = extract_text_from_row(row)
            
            # ID 값 추출 (대부분의 테이블에 id 컬럼이 있다고 가정)
            row_id = row._mapping.get('id', row_index)
            
            # 텍스트 청크 분할
            chunks = split_text_into_chunks(row_text, chunk_size, chunk_overlap)
            
            # 메타데이터와 함께 저장
            for i, chunk in enumerate(chunks):
                chunked_data.append({
                    'text': chunk,
                    'metadata': {
                        'table': table,
                        'row_id': row_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })
    
    return chunked_data