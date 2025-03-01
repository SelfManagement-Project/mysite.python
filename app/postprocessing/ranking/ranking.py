# postprocessing/ranking/ranking.py
from typing import List, Dict, Any

class RankingProcessor:
    def __init__(self, 
                 relevance_weight: float = 0.7, 
                 recency_weight: float = 0.2, 
                 metadata_weight: float = 0.1):
        """
        검색 결과 랭킹 프로세서
        
        Args:
            relevance_weight: 유사도 점수 가중치
            recency_weight: 최신성 가중치
            metadata_weight: 메타데이터 가중치
        """
        self.relevance_weight = relevance_weight
        self.recency_weight = recency_weight
        self.metadata_weight = metadata_weight
    
    def rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        검색 결과를 여러 요소를 고려하여 재정렬
        
        Args:
            results: 유사도 검색 결과 목록
            
        Returns:
            재정렬된 결과 목록
        """
        if not results:
            return []
        
        # 각 결과에 최종 랭킹 점수 계산 및 추가
        ranked_results = []
        for result in results:
            # 1. 기본 유사도 점수 (0-1 사이 값)
            relevance_score = result.get('score', 0)
            
            # 2. 메타데이터 기반 추가 점수 계산
            metadata = result.get('metadata', {})
            
            # 2.1 테이블 타입에 따른 가중치
            table_type_score = self._calculate_table_type_score(metadata.get('table', ''))
            
            # 2.2 데이터 출처에 따른 가중치
            source_score = self._calculate_source_score(metadata)
            
            # 3. 최종 랭킹 점수 계산
            final_score = (
                self.relevance_weight * relevance_score +
                self.metadata_weight * table_type_score + 
                self.metadata_weight * source_score
            )
            
            # 4. 랭킹 점수 추가
            ranked_result = result.copy()
            ranked_result['ranking_score'] = final_score
            ranked_result['original_score'] = relevance_score
            ranked_results.append(ranked_result)
        
        # 최종 점수를 기준으로 내림차순 정렬
        ranked_results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked_results
    
    def _calculate_table_type_score(self, table_name: str) -> float:
        """
        테이블 타입에 따른 가중치 계산
        예: 개인화된 데이터(사용자 일정, 습관 등)가 더 관련성 높음
        """
        high_priority_tables = ['schedule', 'habit', 'chat_history']
        medium_priority_tables = ['user', 'transaction', 'diet']
        
        if table_name.lower() in high_priority_tables:
            return 1.0
        elif table_name.lower() in medium_priority_tables:
            return 0.7
        else:
            return 0.5
    
    def _calculate_source_score(self, metadata: Dict[str, Any]) -> float:
        """
        데이터 출처에 따른 가중치 계산
        예: 사용자 직접 생성 데이터 vs 시스템 생성 데이터
        """
        # 메타데이터에 사용자 ID나 기타 관련 정보가 있는지 확인
        if 'user_id' in metadata:
            return 0.8
        else:
            return 0.5
    
    def rerank_with_custom_rules(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        특정 쿼리나 컨텍스트에 따라 커스텀 규칙 적용
        
        Args:
            results: 기본 랭킹 결과
            query: 원본 쿼리 텍스트
            
        Returns:
            커스텀 규칙이 적용된 결과
        """
        # 기본 랭킹 수행
        ranked_results = self.rank_results(results)
        
        # 쿼리 키워드 기반 추가 가중치 적용
        query_lower = query.lower()
        
        # 예: "일정" 관련 쿼리는 schedule 테이블 우선
        if any(keyword in query_lower for keyword in ["일정", "스케줄", "schedule", "약속"]):
            for result in ranked_results:
                if result.get('metadata', {}).get('table') == 'schedule':
                    result['ranking_score'] *= 1.2
        
        # 예: "습관" 관련 쿼리는 habit 테이블 우선
        elif any(keyword in query_lower for keyword in ["습관", "루틴", "habit", "매일"]):
            for result in ranked_results:
                if result.get('metadata', {}).get('table') == 'habit':
                    result['ranking_score'] *= 1.2
        
        # 재정렬
        ranked_results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked_results