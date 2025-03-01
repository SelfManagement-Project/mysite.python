# services/similarity/search_service.py
from vectordb.qdrant_store import QdrantVectorStore
from data.embedding.embedding import EmbeddingService
from postprocessing.threshold.threshold_filter import ThresholdFilter
from cache.query_cache import QueryCache
from typing import List, Dict, Any, Optional
from postprocessing.ranking.ranking import RankingProcessor

class SearchService:
    def __init__(
        self, 
        vector_store: QdrantVectorStore,
        embedding_service: EmbeddingService,
        threshold_filter: Optional[ThresholdFilter] = None,
        query_cache: Optional[QueryCache] = None,
        ranking_processor: Optional[RankingProcessor] = None,
        cache_enabled: bool = True
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.threshold_filter = threshold_filter or ThresholdFilter()
        self.query_cache = query_cache
        self.ranking_processor = ranking_processor or RankingProcessor()
        self.cache_enabled = cache_enabled
    
    def search(self, query: str, top_k: int = 5, use_cache: bool = True) -> Dict[str, Any]:
        """
        사용자 질문에 대한 유사도 검색 수행
        
        Args:
            query (str): 사용자 질문
            top_k (int): 반환할 최대 결과 수
            use_cache (bool): 캐시 사용 여부
            
        Returns:
            Dict: 검색 결과 및 메타데이터
        """
        # 1. 캐시 확인 (옵션)
        if self.cache_enabled and use_cache and self.query_cache:
            cached_results = self.query_cache.get(query)
            if cached_results:
                return {
                    "status": "success", 
                    "query": query,
                    "results": cached_results,
                    "source": "cache",
                    "filtered": True
                }
        
        # 2. 질문 임베딩 생성
        query_embedding = self.embedding_service.generate_embeddings([query])[0]
        
        # 3. 벡터 검색 수행
        raw_results = self.vector_store.search(query_embedding, top_k * 2)
        
        # 4. 임계값 기반 필터링
        filtered_results = self.threshold_filter.filter_results(raw_results)
        
        # 5. 랭킹 알고리즘 적용 (새로 추가된 부분)
        ranked_results = self.ranking_processor.rerank_with_custom_rules(filtered_results, query)
        
        # 6. 상위 K개만 선택
        top_results = ranked_results[:top_k] if len(ranked_results) > top_k else ranked_results
        
        # 7. 결과 캐싱 (옵션)
        if self.cache_enabled and use_cache and self.query_cache:
            self.query_cache.set(query, top_results)
        
        # 8. 결과 반환
        return {
            "status": "success", 
            "query": query,
            "total_results": len(raw_results),
            "filtered_results": len(filtered_results),
            "results": top_results,
            "threshold": self.threshold_filter.threshold,
            "source": "search"
        }