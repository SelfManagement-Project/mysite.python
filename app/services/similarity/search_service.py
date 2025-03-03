from vectordb.qdrant_store import QdrantVectorStore
from data.embedding.embedding import EmbeddingService
from postprocessing.threshold.threshold_filter import ThresholdFilter
from cache.query_cache import QueryCache
from postprocessing.ranking.ranking import RankingProcessor
from utils.translation_utils import TranslationService
from typing import List, Dict, Any, Optional

class SearchService:
    def __init__(
        self, 
        vector_store: QdrantVectorStore,
        embedding_service: EmbeddingService,
        threshold_filter: Optional[ThresholdFilter] = None,
        query_cache: Optional[QueryCache] = None,
        ranking_processor: Optional[RankingProcessor] = None,
        cache_enabled: bool = True,
        translation_enabled: bool = True
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.threshold_filter = threshold_filter or ThresholdFilter()
        self.query_cache = query_cache
        self.ranking_processor = ranking_processor or RankingProcessor()
        self.cache_enabled = cache_enabled
        self.translation_enabled = translation_enabled
        
        # 번역 서비스 초기화
        if self.translation_enabled:
            self.translation_service = TranslationService(source_lang="ko", target_lang="en")
    
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
        # 원본 쿼리 저장
        original_query = query
        
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
        
        # 2. 질문 번역 (옵션)
        if self.translation_enabled:
            query = self.translation_service.translate_to_target(query)
            print(f"Translated query: {query}")
        
        # 3. 질문 임베딩 생성
        query_embedding = self.embedding_service.generate_embeddings([query], translate=False)[0]
        
        # 4. 벡터 검색 수행
        raw_results = self.vector_store.search(query_embedding, top_k * 2)
        
        # 5. 임계값 기반 필터링
        filtered_results = self.threshold_filter.filter_results(raw_results)
        
        # 6. 랭킹 알고리즘 적용
        ranked_results = self.ranking_processor.rerank_with_custom_rules(filtered_results, original_query)
        
        # 7. 상위 K개만 선택
        top_results = ranked_results[:top_k] if len(ranked_results) > top_k else ranked_results
        
        # 8. 메타데이터 내 텍스트 원래 언어로 번역 (옵션)
        if self.translation_enabled:
            for result in top_results:
                if 'metadata' in result and 'original_text' in result['metadata']:
                    # 원본 텍스트가 있으면 복원
                    result['metadata']['text'] = result['metadata']['original_text']
        
        # 9. 결과 캐싱 (옵션)
        if self.cache_enabled and use_cache and self.query_cache:
            self.query_cache.set(original_query, top_results)
        
        # 10. 결과 반환
        return {
            "status": "success", 
            "query": original_query,
            "total_results": len(raw_results),
            "filtered_results": len(filtered_results),
            "results": top_results,
            "threshold": self.threshold_filter.threshold,
            "source": "search"
        }