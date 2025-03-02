# postprocessing/response/response_processor.py
from typing import Dict, Any, List, Optional
import logging
import time

logger = logging.getLogger(__name__)

class ResponseProcessor:
    """
    LLM 응답을 후처리하는 프로세서 클래스
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        응답 프로세서 초기화
        
        Args:
            config: 응답 처리 설정
        """
        self.config = config or {}
        self.max_response_length = self.config.get("max_response_length", 2000)
        self.add_source_info = self.config.get("add_source_info", True)
        self.filter_harmful_content = self.config.get("filter_harmful_content", True)
        
    def process(self, 
                llm_response: str, 
                context_items: List[Dict[str, Any]],
                query: str) -> Dict[str, Any]:
        """
        LLM 응답에 후처리 단계 적용
        
        Args:
            llm_response: LLM의 원본 텍스트 응답
            context_items: 응답 생성에 사용된 컨텍스트 항목들
            query: 원본 사용자 질의
            
        Returns:
            처리된 응답 객체
        """
        start_time = time.time()
        
        # 기본 응답 객체 구성
        processed_response = {
            "original_response": llm_response,
            "processed_response": llm_response,
            "sources": [],
            "processing_time": 0,
            "filtered": False,
            "enhanced": False
        }
        
        # 1. 응답 콘텐츠 검증 및 필터링
        if self.filter_harmful_content:
            processed_response = self._filter_content(processed_response)
        
        # 2. 응답 개선
        processed_response = self._enhance_response(processed_response, context_items, query)
        
        # 3. 응답 길이 제한
        if len(processed_response["processed_response"]) > self.max_response_length:
            processed_response["processed_response"] = processed_response["processed_response"][:self.max_response_length] + "..."
        
        # 4. 출처 정보 추가
        if self.add_source_info:
            processed_response = self._add_source_info(processed_response, context_items)
            
        # 처리 시간 계산
        processed_response["processing_time"] = time.time() - start_time
        
        logger.debug(f"Response processed in {processed_response['processing_time']:.4f}s")
        return processed_response
        
    def _filter_content(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        유해하거나 부적절한 콘텐츠 필터링
        """
        # 간단한 키워드 기반 필터링 (실제 구현에서는 더 정교한 시스템 사용)
        harmful_keywords = ["비밀번호", "주민등록번호", "비용", "금액", "계좌정보", "결제정보"]
        
        processed_text = response["processed_response"]
        for keyword in harmful_keywords:
            if keyword in processed_text:
                processed_text = processed_text.replace(keyword, "[필터링됨]")
                response["filtered"] = True
        
        response["processed_response"] = processed_text
        return response
        
    def _enhance_response(self, 
                         response: Dict[str, Any], 
                         context_items: List[Dict[str, Any]],
                         query: str) -> Dict[str, Any]:
        """
        응답 품질 개선 (컨텍스트 항목 활용)
        """
        # 현재는 간단한 구현만 제공
        # 실제 시스템에서는 여기에 더 정교한 개선 로직 추가 가능
        
        # 관련된 표나 데이터가 있으면 응답에 추가
        return response
            
    def _add_source_info(self, 
                        response: Dict[str, Any], 
                        context_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        응답에 출처 정보 추가
        """
        # 상위 3개 관련 출처 추가
        if context_items:
            sources = []
            added_tables = set()  # 중복 출처 방지
            
            for item in context_items[:5]:  # 상위 5개 항목 검토
                metadata = item.get('metadata', {})
                table = metadata.get('table', '')
                
                if table and table not in added_tables:
                    source_info = {
                        "table": table,
                        "relevance": item.get('score', 0),
                    }
                    sources.append(source_info)
                    added_tables.add(table)
                    
                    # 최대 3개 출처만 추가
                    if len(sources) >= 3:
                        break
            
            response["sources"] = sources
        
        return response