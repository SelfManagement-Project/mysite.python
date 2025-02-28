# postprocessing/threshold/threshold_filter.py
from typing import List, Dict, Any

class ThresholdFilter:
    def __init__(self, threshold: float = 0.7):
        """
        임계값(threshold) 기반 필터링 클래스
        
        Args:
            threshold (float): 유사도 점수 임계값 (0~1 사이, 높을수록 더 엄격한 필터링)
        """
        self.threshold = threshold
    
    def filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        임계값 이상의 유사도 점수를 가진 결과만 반환
        
        Args:
            results (List[Dict]): 벡터 검색 결과 리스트
            
        Returns:
            List[Dict]: 필터링된 결과 리스트
        """
        # Qdrant에서는 높은 점수가 더 관련성이 높음 (코사인 유사도)
        filtered_results = [
            result for result in results 
            if result.get('score', 0) >= self.threshold
        ]
        
        return filtered_results