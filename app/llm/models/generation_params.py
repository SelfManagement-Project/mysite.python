# llm/models/generation_params.py
from typing import Dict, Any, Optional, List
import json
import os

class GenerationParameters:
    """
    LLM 응답 생성 파라미터 관리 클래스
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        LLM 생성 파라미터 관리자 초기화
        
        Args:
            config_path: 기본 설정 파일 경로 (없으면 기본값 사용)
        """
        # 기본 설정
        self.default_params = {
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1.05,
            "do_sample": True
        }
        
        # 용도별 프리셋
        self.presets = {
            "creative": {
                "temperature": 0.9,
                "top_p": 0.95,
                "repetition_penalty": 1.03
            },
            "precise": {
                "temperature": 0.2,
                "top_p": 0.85,
                "repetition_penalty": 1.1
            },
            "balanced": self.default_params.copy()
        }
        
        # 설정 파일이 있으면 로드
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """
        설정 파일 로드
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 기본 설정 업데이트
                if 'default' in config:
                    self.default_params.update(config['default'])
                
                # 프리셋 업데이트
                if 'presets' in config:
                    for preset_name, preset_params in config['presets'].items():
                        if preset_name in self.presets:
                            self.presets[preset_name].update(preset_params)
                        else:
                            self.presets[preset_name] = preset_params
        except Exception as e:
            print(f"설정 파일 로드 중 오류 발생: {e}")
    
    def get_params(self, 
                 preset: Optional[str] = None, 
                 overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        LLM 생성 파라미터 가져오기
        
        Args:
            preset: 사용할 프리셋 이름 (없으면 기본값 사용)
            overrides: 개별 설정값 (프리셋보다 우선)
            
        Returns:
            LLM 생성 파라미터 설정
        """
        # 기본 파라미터 복사
        params = self.default_params.copy()
        
        # 프리셋 적용
        if preset and preset in self.presets:
            params.update(self.presets[preset])
        
        # 개별 설정 적용
        if overrides:
            params.update(overrides)
            
        return params
    
    def create_adaptive_params(self, 
                             query: str, 
                             context_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        쿼리와 컨텍스트에 따라 적응형 파라미터 생성
        
        Args:
            query: 사용자 쿼리
            context_items: 검색된 컨텍스트 항목
            
        Returns:
            적응형 LLM 생성 파라미터
        """
        # 기본 파라미터 시작
        params = self.default_params.copy()
        
        # 1. 쿼리 복잡성에 따른 조정
        query_length = len(query)
        if query_length > 100:  # 긴 질문은 더 정확한 응답 필요
            params['temperature'] = 0.3
            params['repetition_penalty'] = 1.1
        elif query_length < 20:  # 짧은 질문은 더 창의적 응답 가능
            params['temperature'] = 0.8
        
        # 2. 컨텍스트 품질에 따른 조정
        if context_items:
            avg_score = sum(item.get('score', 0) for item in context_items) / len(context_items)
            
            # 높은 관련성 점수 컨텍스트는 정확한 응답 생성
            if avg_score > 0.8:
                params['temperature'] = max(0.2, params['temperature'] - 0.2)
            # 낮은 관련성 점수는 더 창의적 응답 필요
            elif avg_score < 0.4:
                params['temperature'] = min(0.9, params['temperature'] + 0.2)
        
        # 3. 쿼리 키워드 기반 조정
        creative_keywords = ['아이디어', '창의적', '제안', '생각', '상상']
        precise_keywords = ['정확한', '사실', '데이터', '분석', '요약']
        
        if any(keyword in query for keyword in creative_keywords):
            params['temperature'] = 0.85
            params['top_p'] = 0.92
        elif any(keyword in query for keyword in precise_keywords):
            params['temperature'] = 0.3
            params['top_p'] = 0.85
        
        return params