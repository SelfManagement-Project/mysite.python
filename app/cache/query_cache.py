# cache/query_cache.py
import hashlib
import json
from typing import Dict, Any, Optional
import time

class QueryCache:
    def __init__(self, ttl: int = 3600):  # 기본 캐시 유효시간 1시간
        self.cache = {}
        self.ttl = ttl
    
    def _generate_key(self, query: str) -> str:
        """쿼리 문자열에서 캐시 키 생성"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """쿼리에 대한 캐시된 결과 가져오기"""
        key = self._generate_key(query)
        if key in self.cache:
            cache_entry = self.cache[key]
            # 캐시 만료 확인
            if time.time() < cache_entry['expires_at']:
                return cache_entry['results']
            else:
                # 만료된 캐시 항목 삭제
                del self.cache[key]
        return None
    
    def set(self, query: str, results: Dict[str, Any]) -> None:
        """쿼리 결과를 캐시에 저장"""
        key = self._generate_key(query)
        self.cache[key] = {
            'results': results,
            'expires_at': time.time() + self.ttl
        }
    
    def clear(self) -> None:
        """캐시 전체 비우기"""
        self.cache = {}