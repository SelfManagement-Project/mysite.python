# llm/prompts/chat_prompt.py
from typing import List, Dict, Any

class PromptTemplate:
    @staticmethod
    def create_prompt_from_context(query: str, context_items: List[Dict[str, Any]]) -> str:
        """
        검색된 컨텍스트와 사용자 질문을 바탕으로 프롬프트 생성
        
        Args:
            query: 사용자 질문
            context_items: 검색된 컨텍스트 항목 리스트
            
        Returns:
            최종 프롬프트 문자열
        """
        # 컨텍스트 정보 추출
        context_texts = []
        for item in context_items:
            metadata = item.get('metadata', {})
            text = metadata.get('text', '')
            table = metadata.get('table', 'unknown')
            source_info = f"[출처: {table}]"
            
            if text:
                context_texts.append(f"{text} {source_info}")
        
        # 컨텍스트 결합
        combined_context = "\n".join(context_texts)
        
        # 최종 프롬프트 구성
        prompt = f"""당신은 개인 종합 관리 플랫폼의 지능형 비서입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.
                다음은 사용자의 데이터베이스에서 추출한 관련 정보입니다:

                ---
                {combined_context}
                ---

                위 정보를 바탕으로 다음 질문에 답변해주세요:
                질문: {query}

                답변:"""
        
        return prompt