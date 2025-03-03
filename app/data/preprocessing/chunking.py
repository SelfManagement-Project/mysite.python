# data/preprocessing/chunking.py
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any
from utils.translation_utils import TranslationService

translation_service = TranslationService(source_lang="ko", target_lang="en")
translation_enabled = True  # 전역 설정

def get_all_tables(db: Session):
    """데이터베이스의 모든 테이블 이름 가져오기"""
    inspector = inspect(db.bind)
    return inspector.get_table_names()

def fetch_data_from_table(db: Session, table_name: str, limit: int = None):
    """특정 테이블에서 데이터 가져오기"""
    query = f'SELECT * FROM "{table_name}"' + (f" LIMIT {limit}" if limit else "")
    result = db.execute(text(query))
    return result.fetchall()

def extract_text_from_row(row, translate: bool = None):
    """
    DB 로우에서 텍스트 데이터 추출 및 번역 (선택 사항)
    """
    if translate is None:
        translate = translation_enabled
    
    row_dict = row._mapping
    text_parts = []
    
    for key, value in row_dict.items():
        if value is not None:  # None 값 제외
            text_parts.append(f"{key}: {value}")
    
    text = " | ".join(text_parts)
    
    # 번역 옵션이 활성화된 경우 영어로 번역
    if translate:
        original_text = text
        text = translation_service.translate_to_target(text)
        print(f"원본 텍스트: {original_text}")
        print(f"번역된 텍스트: {text}")
    
    return text

# data/preprocessing/chunking.py - split_text_into_chunks 함수 추가
def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    텍스트를 일정 크기의 청크로 분할
    
    Args:
        text: 분할할 텍스트
        chunk_size: 각 청크의 최대 길이
        chunk_overlap: 연속 청크 간의 중복 문자 수
        
    Returns:
        분할된 청크 목록
    """
    # 텍스트가 충분히 짧으면 그대로 반환
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # 청크의 끝 위치 계산
        end = start + chunk_size
        
        # 텍스트의 끝에 도달한 경우
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # 단어 경계에서 분할하기 위해 끝 위치 조정
        # 공백을 찾을 때까지 뒤로 이동
        while end > start and text[end] != ' ':
            end -= 1
        
        # 공백을 찾지 못한 경우 원래 위치 사용
        if end == start:
            end = start + chunk_size
        
        # 청크 추가
        chunks.append(text[start:end])
        
        # 다음 시작 위치 (중복 고려)
        start = end - chunk_overlap
        
        # 시작 위치가 앞으로 가지 않도록 보정
        if start < end - chunk_size:
            start = end
    
    return chunks

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