from typing import List, Dict, Any
from utils.translation_utils import TranslationService

class TranslationPreprocessor:
    """데이터 전처리를 위한 번역 클래스"""
    
    def __init__(self):
        """번역 전처리기 초기화"""
        self.translation_service = TranslationService(source_lang="ko", target_lang="en")
    
    def translate_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """DB 로우 데이터 번역"""
        translated_row = {}
        
        for key, value in row.items():
            # 숫자, 날짜 등은 그대로 유지
            if not isinstance(value, str):
                translated_row[key] = value
                continue
                
            # 문자열 필드만 번역
            if len(value.strip()) > 0:
                # 원본 값 보존
                translated_row[f"original_{key}"] = value
                # 번역된 값 저장
                translated_row[key] = self.translation_service.translate_to_target(value)
            else:
                translated_row[key] = value
                
        return translated_row
    
    def translate_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """청크 데이터 번역"""
        translated_chunk = chunk.copy()
        
        # 텍스트 필드 번역
        if 'text' in translated_chunk and translated_chunk['text']:
            translated_chunk['original_text'] = translated_chunk['text']
            translated_chunk['text'] = self.translation_service.translate_to_target(translated_chunk['text'])
            
        # 메타데이터 내의 텍스트 필드 번역
        if 'metadata' in translated_chunk and translated_chunk['metadata']:
            if 'text' in translated_chunk['metadata'] and translated_chunk['metadata']['text']:
                translated_chunk['metadata']['original_text'] = translated_chunk['metadata']['text']
                translated_chunk['metadata']['text'] = self.translation_service.translate_to_target(
                    translated_chunk['metadata']['text']
                )
                
        return translated_chunk