# services/chat/chat_service.py
from llm.models.deepseek_model import DeepSeekLLM
from llm.prompts.chat_prompt import PromptTemplate
from services.similarity.search_service import SearchService
from typing import Dict, Any, Optional, List

class ChatService:
    def __init__(self, 
                 search_service: SearchService, 
                 llm_model: Optional[DeepSeekLLM] = None,
                 max_context_items: int = 5):
        """
        챗봇 서비스 초기화
        
        Args:
            search_service: 벡터 검색 서비스
            llm_model: LLM 모델 인스턴스
            max_context_items: 프롬프트에 포함할 최대 컨텍스트 항목 수
        """
        self.search_service = search_service
        self.llm_model = llm_model if llm_model else DeepSeekLLM()
        self.max_context_items = max_context_items
        
    def process_message(self, 
                        message: str, 
                        user_id: int, 
                        chat_id: Optional[int] = None, 
                        search_threshold: float = 0.45) -> Dict[str, Any]:
        """
        사용자 메시지 처리 및 응답 생성
        
        Args:
            message: 사용자 메시지
            user_id: 사용자 ID
            chat_id: 채팅 ID (선택 사항)
            search_threshold: 검색 임계값
            
        Returns:
            응답 정보
        """
        # 1. 벡터 검색 수행
        search_results = self.search_service.search(
            query=message, 
            top_k=self.max_context_items, 
            use_cache=True
        )
        
        # 검색 결과 가져오기
        context_items = search_results.get('results', [])
        
        # 2. 프롬프트 생성
        prompt = PromptTemplate.create_prompt_from_context(
            query=message,
            context_items=context_items
        )
        
        # 3. LLM으로 응답 생성
        llm_response = self.llm_model.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7
        )
        
        # 4. 응답 구성
        response = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message": message,
            "response": llm_response,
            "context_items": [item.get('metadata', {}).get('text', '') for item in context_items[:3]],  # 디버깅용 컨텍스트 일부 반환
            "status": "success"
        }
        
        return response