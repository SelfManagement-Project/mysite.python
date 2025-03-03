import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from utils.translation_utils import TranslationService

class EmbeddingService:
    def __init__(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        """임베딩 서비스 초기화"""
        self.model = SentenceTransformer(model_name)
        self.translation_service = TranslationService(source_lang="ko", target_lang="en")
    
    def generate_embeddings(self, texts: List[str], translate: bool = True) -> List[np.ndarray]:
        """텍스트 리스트에 대한 임베딩 생성"""
        if translate:
            # 영어로 번역 후 임베딩
            translated_texts = self.translation_service.translate_batch_to_target(texts)
            embeddings = self.model.encode(translated_texts)
        else:
            # 직접 임베딩 (번역 없음)
            embeddings = self.model.encode(texts)
        return embeddings
    
    def process_chunks(self, chunked_data: List[Dict[str, Any]], translate: bool = True) -> List[Dict[str, Any]]:
        """청크 데이터에 임베딩 추가"""
        # 텍스트만 추출
        texts = [chunk["text"] for chunk in chunked_data]
        
        if translate:
            # 영어로 번역
            translated_texts = self.translation_service.translate_batch_to_target(texts)
            
            # 원본 텍스트 저장
            for i, chunk in enumerate(chunked_data):
                chunk["original_text"] = chunk["text"]
                chunk["text"] = translated_texts[i]
            
            # 번역된 텍스트로 임베딩 생성
            embeddings = self.model.encode(translated_texts)
        else:
            # 번역 없이 임베딩 생성
            embeddings = self.model.encode(texts)
        
        # 임베딩을 원래 데이터와 결합
        for i, chunk in enumerate(chunked_data):
            chunk["embedding"] = embeddings[i].tolist()  # numpy 배열을 리스트로 변환
        
        return chunked_data