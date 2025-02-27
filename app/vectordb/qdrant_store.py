# vectorstore/qdrant_store.py
from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import numpy as np
import uuid

class QdrantVectorStore:
    def __init__(self, collection_name: str = "chatbot_vectors", vector_size: int = 384):
        """Qdrant 벡터 저장소 초기화"""
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # 컬렉션이 존재하는지 확인하고 없으면 생성
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self._create_collection()
    
    def _create_collection(self):
        """HNSW 인덱스를 사용하는 새 컬렉션 생성"""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
            hnsw_config=models.HnswConfigDiff(
                m=16,                 # HNSW 그래프의 최대 연결 수
                ef_construct=100,     # 인덱싱 품질 (높을수록 품질↑, 속도↓)
                full_scan_threshold=10000  # 전체 스캔 임계값
            )
        )
    
    def add_embeddings(self, embeddings: List[np.ndarray], metadatas: List[Dict[str, Any]]):
        """임베딩 벡터와 메타데이터 추가"""
        if len(embeddings) == 0:
            return
        
        # 각 임베딩에 대한 고유 ID 생성
        ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]
        
        # 점수 및 페이로드 준비
        vectors = [embedding.tolist() for embedding in embeddings]
        payloads = []
        
        for i, metadata in enumerate(metadatas):
            # 메타데이터에 원본 텍스트 추가
            payloads.append({
                **metadata,
                "vector_id": ids[i]
            })
        
        # Qdrant에 데이터 추가
        self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads
            )
        )
        
        return {"inserted": len(ids), "ids": ids}
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """쿼리 벡터와 유사한 벡터 검색"""
        query_vector = query_embedding.tolist()
        
        # 검색 수행
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        # 결과 정리
        results = []
        for hit in search_result:
            results.append({
                'id': hit.id,
                'score': hit.score,
                'metadata': hit.payload
            })
        
        return results
    
    def count(self) -> int:
        """저장된 벡터 수 반환"""
        collection_info = self.client.get_collection(self.collection_name)
        return collection_info.vectors_count
    
    def delete_by_metadata(self, table: str, row_id: int):
        """특정 테이블과 레코드 ID에 해당하는 모든 벡터 삭제"""
        filter_obj = models.Filter(
            must=[
                models.FieldCondition(
                    key="table",
                    match=models.MatchValue(value=table)
                ),
                models.FieldCondition(
                    key="row_id",
                    match=models.MatchValue(value=row_id)
                )
            ]
        )
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=filter_obj)
        )