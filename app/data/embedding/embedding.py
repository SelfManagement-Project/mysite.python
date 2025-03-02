# data/embedding/embedding.py
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        """임베딩 서비스 초기화 - 다국어 지원 모델로 변경"""
        self.model = SentenceTransformer(model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """텍스트 리스트에 대한 임베딩 생성"""
        embeddings = self.model.encode(texts)
        return embeddings
    
    def process_chunks(self, chunked_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """청크 데이터에 임베딩 추가"""
        # 텍스트만 추출
        texts = [chunk["text"] for chunk in chunked_data]
        
        # 임베딩 생성
        embeddings = self.generate_embeddings(texts)
        
        # 임베딩을 원래 데이터와 결합
        for i, chunk in enumerate(chunked_data):
            chunk["embedding"] = embeddings[i].tolist()  # numpy 배열을 리스트로 변환
        
        return chunked_data