# postprocessing/formatter/response_formatter.py
from typing import Dict, Any, List, Optional
import re

class ResponseFormatter:
    """
    응답 형식을 조정하는 클래스
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        응답 포맷터 초기화
        
        Args:
            config: 포맷 설정
        """
        self.config = config or {}
        self.format_type = self.config.get("format_type", "default")
        self.enable_markdown = self.config.get("enable_markdown", True)
        
    def format(self, 
              processed_response: Dict[str, Any], 
              output_format: Optional[str] = None) -> Dict[str, Any]:
        """
        처리된 응답을 지정된 형식으로 포맷팅
        
        Args:
            processed_response: 처리된 응답 객체
            output_format: 출력 형식 (None인 경우 기본 설정 사용)
            
        Returns:
            포맷팅된 응답 객체
        """
        # 사용할 형식 결정
        format_type = output_format or self.format_type
        
        # 응답 복사본 생성
        formatted_response = processed_response.copy()
        
        # 형식에 따라 처리
        if format_type == "simple":
            formatted_response = self._format_simple(formatted_response)
        elif format_type == "detailed":
            formatted_response = self._format_detailed(formatted_response)
        elif format_type == "markdown":
            formatted_response = self._format_markdown(formatted_response)
        else:  # default
            formatted_response = self._format_default(formatted_response)
            
        return formatted_response
    
    def _format_default(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        기본 형식으로 응답 포맷팅
        """
        # 출처 정보가 있으면 응답 하단에 추가
        if response.get("sources") and len(response["sources"]) > 0:
            text = response["processed_response"]
            
            # 출처 정보 문자열 생성
            source_text = "\n\n참고 출처: "
            for i, source in enumerate(response["sources"]):
                if i > 0:
                    source_text += ", "
                source_text += f"{source['table']}"
            
            # 응답에 출처 정보 추가
            response["formatted_response"] = text + source_text
        else:
            response["formatted_response"] = response["processed_response"]
            
        return response
    
    def _format_simple(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        간단한 형식으로 응답 포맷팅 (출처 정보 제외)
        """
        response["formatted_response"] = response["processed_response"]
        return response
    
    def _format_detailed(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        상세 형식으로 응답 포맷팅 (출처 정보 및 신뢰도 포함)
        """
        text = response["processed_response"]
        
        # 출처 정보 상세 포함
        if response.get("sources") and len(response["sources"]) > 0:
            source_text = "\n\n출처 정보:\n"
            for i, source in enumerate(response["sources"]):
                source_text += f"{i+1}. {source['table']} (관련도: {source['relevance']:.2f})\n"
            
            # 응답에 출처 정보 추가
            text += source_text
        
        response["formatted_response"] = text
        return response
    
    def _format_markdown(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        마크다운 형식으로 응답 포맷팅
        """
        if not self.enable_markdown:
            return self._format_default(response)
            
        text = response["processed_response"]
        
        # 기본 마크다운 서식 적용 (필요에 따라 확장)
        # 제목 서식 적용
        text = re.sub(r'^(?!#)(.+)(?:\n|$)', r'## \1\n', text, flags=re.MULTILINE, count=1)
        
        # 출처 정보 마크다운으로 포맷팅
        if response.get("sources") and len(response["sources"]) > 0:
            source_text = "\n\n**참고 출처:**\n"
            for i, source in enumerate(response["sources"]):
                source_text += f"- {source['table']}\n"
            
            text += source_text
        
        response["formatted_response"] = text
        return response