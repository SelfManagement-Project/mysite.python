# postprocessing/validation/validation.py
from typing import Dict, Any, List, Optional, Tuple
import re

class ResponseValidator:
    """
    LLM 응답을 검증하는 클래스
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        응답 검증기 초기화
        
        Args:
            config: 검증 설정
        """
        self.config = config or {}
        self.min_length = self.config.get("min_length", 10)
        self.max_length = self.config.get("max_length", 2000)
        self.check_hallucination = self.config.get("check_hallucination", True)
        
    def validate(self, 
                response: str, 
                context_items: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        응답 검증 수행
        
        Args:
            response: LLM 응답 텍스트
            context_items: 응답 생성에 사용된 컨텍스트 항목들
            
        Returns:
            (검증 통과 여부, 오류 메시지 목록) 튜플
        """
        issues = []
        
        # 1. 길이 검증
        if len(response) < self.min_length:
            issues.append(f"응답이 너무 짧습니다. (최소 {self.min_length}자)")
        
        if len(response) > self.max_length:
            issues.append(f"응답이 너무 깁니다. (최대 {self.max_length}자)")
            
        # 2. 완전성 검증
        if not self._check_completeness(response):
            issues.append("응답이 불완전합니다.")
        
        # 3. 환각(hallucination) 검증 (컨텍스트에 없는 정보 언급)
        if self.check_hallucination:
            hallucination_issues = self._check_hallucination(response, context_items)
            issues.extend(hallucination_issues)
            
        # 4. 의미론적 일관성 검증
        consistency_issues = self._check_semantic_consistency(response)
        issues.extend(consistency_issues)
        
        # 검증 결과 반환
        return len(issues) == 0, issues
    
    def _check_completeness(self, response: str) -> bool:
        """
        응답 완전성 검증
        """
        # 문장이 갑자기 끊기지 않았는지 확인
        if response.endswith(('...', '…')):
            return False
            
        # 마지막 문장이 완전한지 확인 (마침표, 물음표, 느낌표 등으로 끝남)
        if not re.search(r'[.!?]\s*$', response):
            return False
            
        return True
    
    def _check_hallucination(self, 
                            response: str, 
                            context_items: List[Dict[str, Any]]) -> List[str]:
        """
        환각(hallucination) 현상 검증
        """
        # 이 부분은 실제 구현이 복잡할 수 있습니다.
        # 간단한 예시만 제공합니다.
        issues = []
        
        # 컨텍스트에서 핵심 정보 추출
        key_info = set()
        for item in context_items:
            metadata = item.get('metadata', {})
            text = metadata.get('text', '')
            
            # 다양한 정보 추출 (실제 구현에서는 더 정교한 방법 필요)
            # 예: 숫자, 날짜, 장소, 이름 등 추출
            
            # 간단한 예: 숫자 추출
            numbers = re.findall(r'\d+', text)
            key_info.update(numbers)
        
        # 응답에서 사용된 숫자가 컨텍스트에 있는지 확인
        response_numbers = re.findall(r'\d+', response)
        
        for number in response_numbers:
            if number not in key_info and len(number) > 3:  # 간단한 필터링 (4자리 이상 숫자)
                issues.append(f"응답에 컨텍스트에 없는 숫자가 포함되어 있음: {number}")
        
        return issues
    
    def _check_semantic_consistency(self, response: str) -> List[str]:
        """
        의미론적 일관성 검증
        """
        issues = []
        
        # 간단한 모순 패턴 검사 (실제 구현에서는 더 정교한 방법 필요)
        contradiction_patterns = [
            (r'맞습니다.*\b아닙니다\b', "긍정과 부정이 혼재되어 있습니다."),
            (r'아닙니다.*\b맞습니다\b', "부정과 긍정이 혼재되어 있습니다."),
            (r'없습니다.*\b있습니다\b', "없음과 있음이 혼재되어 있습니다."),
            (r'있습니다.*\b없습니다\b', "있음과 없음이 혼재되어 있습니다.")
        ]
        
        for pattern, message in contradiction_patterns:
            if re.search(pattern, response):
                issues.append(message)
        
        return issues