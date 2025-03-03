from typing import List, Dict, Any, Optional
from deep_translator import GoogleTranslator

class TranslationService:
    """번역 서비스 유틸리티 클래스"""
    
    def __init__(self, source_lang="ko", target_lang="en"):
        """번역 서비스 초기화"""
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        # 역방향 번역기도 초기화 (영어 -> 한국어)
        self.reverse_translator = GoogleTranslator(source="en", target="ko")
        
    def translate_to_target(self, text: str) -> str:
        """소스 언어에서 타겟 언어로 텍스트 번역"""
        if not text or not isinstance(text, str):
            return ""
            
        try:
            return self.translator.translate(text)
        except Exception as e:
            print(f"번역 오류 (소스 -> 타겟): {e}")
            return text
    
    def translate_to_source(self, text: str) -> str:
        """타겟 언어에서 소스 언어로 텍스트 번역"""
        if not text or not isinstance(text, str):
            return ""
            
        try:
            return self.reverse_translator.translate(text)
        except Exception as e:
            print(f"번역 오류 (타겟 -> 소스): {e}")
            return text
    
    def translate_batch_to_target(self, texts: List[str]) -> List[str]:
        """텍스트 배치를 타겟 언어로 번역"""
        return [self.translate_to_target(text) for text in texts if text]
    
    def translate_batch_to_source(self, texts: List[str]) -> List[str]:
        """텍스트 배치를 소스 언어로 번역"""
        return [self.translate_to_source(text) for text in texts if text]
    
    def translate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 필드 번역"""
        translated_metadata = metadata.copy()
        # 텍스트 필드만 번역
        if 'text' in translated_metadata and translated_metadata['text']:
            translated_metadata['original_text'] = translated_metadata['text']
            translated_metadata['text'] = self.translate_to_target(translated_metadata['text'])
        return translated_metadata