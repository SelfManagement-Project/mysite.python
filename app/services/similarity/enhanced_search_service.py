# services/similarity/enhanced_search_service.py
from typing import Dict, Any, List, Optional
from services.similarity.search_service import SearchService
from vectordb.qdrant_store import QdrantVectorStore
from data.embedding.embedding import EmbeddingService
from postprocessing.threshold.threshold_filter import ThresholdFilter
from postprocessing.ranking.ranking import RankingProcessor
from cache.query_cache import QueryCache
import datetime

class EnhancedSearchService(SearchService):
    """
    향상된 검색 서비스 - 특수 기능 및 메타데이터 기반 필터링 기능 추가
    """
    
    def __init__(self, 
                 vector_store: QdrantVectorStore, 
                 embedding_service: EmbeddingService,
                 threshold_filter: ThresholdFilter,
                 query_cache: Optional[QueryCache] = None,
                 ranking_processor: Optional[RankingProcessor] = None):
        """
        향상된 검색 서비스 초기화
        """
        super().__init__(
            vector_store=vector_store,
            embedding_service=embedding_service,
            threshold_filter=threshold_filter,
            query_cache=query_cache,
            ranking_processor=ranking_processor
        )
    
    def search_with_criteria(self, 
                           query: str, 
                           top_k: int = 5, 
                           use_cache: bool = True,
                           criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        특정 기준에 따라 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            use_cache: 캐시 사용 여부
            criteria: 검색 기준 (recency, source_priority, user_relevance 등)
            
        Returns:
            검색 결과 및 메타데이터
        """
        # 기본 검색 결과 가져오기
        base_results = self.search(query, top_k, use_cache)
        
        # 기준이 없으면 기본 결과 반환
        if not criteria:
            return base_results
            
        # 검색 결과 리스트
        results = base_results.get('results', [])
        
        # 결과가 없으면 기본 결과 반환
        if not results:
            return base_results
            
        # 기준에 따라 결과 재정렬
        sorted_results = self._apply_sorting_criteria(results, criteria)
        
        # 결과 업데이트
        base_results['results'] = sorted_results
        base_results['applied_criteria'] = criteria
        
        return base_results
    
    def _apply_sorting_criteria(self, 
                              results: List[Dict[str, Any]], 
                              criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        특정 기준에 따라 결과 정렬
        
        Args:
            results: 검색 결과 리스트
            criteria: 정렬 기준
            
        Returns:
            정렬된 결과 리스트
        """
        # 결과 복사본 생성
        sorted_results = results.copy()
        
        # 1. 최신성 기준 정렬
        if criteria.get('recency'):
            weight = criteria.get('recency_weight', 1.0)
            date_field = criteria.get('date_field', 'created_at')
            sorted_results = self._sort_by_recency(sorted_results, weight, date_field)
            
        # 2. 출처 우선순위 기준 정렬
        if criteria.get('source_priority'):
            weight = criteria.get('source_weight', 1.0)
            priority_sources = criteria.get('priority_sources', [])
            sorted_results = self._sort_by_source_priority(sorted_results, weight, priority_sources)
            
        # 3. 사용자 관련성 기준 정렬
        if criteria.get('user_relevance'):
            weight = criteria.get('user_weight', 1.0)
            user_id = criteria.get('user_id')
            sorted_results = self._sort_by_user_relevance(sorted_results, weight, user_id)
            
        return sorted_results
        
    def _sort_by_recency(self, 
                       results: List[Dict[str, Any]],
                       weight: float,
                       date_field: str) -> List[Dict[str, Any]]:
        """
        최신성에 따라 결과 정렬
        """
        # 현재 날짜/시간
        now = datetime.datetime.now()
        
        # 각 결과에 최신성 점수 추가
        for result in results:
            metadata = result.get('metadata', {})
            date_str = metadata.get(date_field)
            
            # 날짜 정보가 있는 경우 최신성 점수 계산
            recency_score = 0.0
            if date_str:
                try:
                    # 날짜 문자열 파싱 (ISO 형식 가정)
                    date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    # 최신성 점수 계산 (최대 30일 기준)
                    days_diff = (now - date_obj).days
                    if days_diff <= 0:
                        recency_score = 1.0
                    elif days_diff <= 30:
                        recency_score = 1.0 - (days_diff / 30)
                    else:
                        recency_score = 0.0
                except ValueError:
                    pass
            
            # 기존 점수와 최신성 점수 결합
            original_score = result.get('ranking_score', result.get('score', 0))
            result['ranking_score'] = original_score * (1.0 - weight) + recency_score * weight
            result['recency_score'] = recency_score
        
        # 최종 점수로 정렬
        results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
        return results
        
    def _sort_by_source_priority(self, 
                              results: List[Dict[str, Any]],
                              weight: float,
                              priority_sources: List[str]) -> List[Dict[str, Any]]:
        """
        출처 우선순위에 따라 결과 정렬
        """
        # 각 결과에 출처 우선순위 점수 추가
        for result in results:
            metadata = result.get('metadata', {})
            table = metadata.get('table', '')
            
            # 우선순위 점수 계산
            source_score = 0.0
            if table in priority_sources:
                source_score = 1.0 - (priority_sources.index(table) / len(priority_sources))
            
            # 기존 점수와 출처 점수 결합
            original_score = result.get('ranking_score', result.get('score', 0))
            result['ranking_score'] = original_score * (1.0 - weight) + source_score * weight
            result['source_score'] = source_score
        
        # 최종 점수로 정렬
        results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
        return results
        
    def _sort_by_user_relevance(self, 
                             results: List[Dict[str, Any]],
                             weight: float,
                             user_id: Optional[int]) -> List[Dict[str, Any]]:
        """
        사용자 관련성에 따라 결과 정렬
        """
        if not user_id:
            return results
            
        # 각 결과에 사용자 관련성 점수 추가
        for result in results:
            metadata = result.get('metadata', {})
            result_user_id = metadata.get('user_id')
            
            # 사용자 관련성 점수 계산
            user_score = 1.0 if str(result_user_id) == str(user_id) else 0.2
            
            # 기존 점수와 사용자 관련성 점수 결합
            original_score = result.get('ranking_score', result.get('score', 0))
            result['ranking_score'] = original_score * (1.0 - weight) + user_score * weight
            result['user_score'] = user_score
        
        # 최종 점수로 정렬
        results.sort(key=lambda x: x.get('ranking_score', 0), reverse=True)
        return results