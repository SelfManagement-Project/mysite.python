# llm/prompts/chat_prompt.py
from typing import List, Dict, Any, Optional

class PromptTemplate:
    @staticmethod
    def create_prompt_from_context(
        query: str, 
        context_items: List[Dict[str, Any]], 
        format_type: Optional[str] = "default"
    ) -> str:
        """
        검색된 컨텍스트와 사용자 질문을 바탕으로 프롬프트 생성
        
        Args:
            query: 사용자 질문
            context_items: 검색된 컨텍스트 항목 리스트
            format_type: 응답 형식 타입 (default, detailed, simple)
            
        Returns:
            최종 프롬프트 문자열
        """
        # 컨텍스트 정보 추출 및 관련성 점수에 따라 정렬
        context_with_score = []
        for item in context_items:
            metadata = item.get('metadata', {})
            text = metadata.get('text', '')
            table = metadata.get('table', 'unknown')
            score = item.get('score', 0)
            
            if text:
                context_with_score.append((text, table, score))
        
        # 관련성 점수로 내림차순 정렬
        context_with_score.sort(key=lambda x: x[2], reverse=True)
        
        # 정렬된 컨텍스트로 텍스트 구성
        context_texts = []
        for text, table, _ in context_with_score:
            context_texts.append(f"[출처: {table}] {text}")
        
        # 컨텍스트 결합
        combined_context = "\n\n".join(context_texts)
        
        # 응답 형식에 따른 프롬프트 구성
        system_prompt = """당신은 개인 종합 관리 플랫폼의 지능형 비서입니다. 사용자가 한국어로 질문하면 한국어로 답변하세요. 사용자의 일정, 습관, 대화 기록 등의 정보를 바탕으로 명확하고 도움이 되는 답변을 제공해야 합니다.

                        응답 작성 시 다음 규칙을 반드시 준수하세요:
                        1. 제공된 정보만 사용하여 답변하고, 없는 정보는 추측하지 마세요.
                        2. 자연스러운 한국어로 완전한 문장을 사용하세요.
                        3. 내부 분석 과정이나 생각을 드러내지 마세요 (예: "이 쿼리는...", "정보를 찾아보니..." 등의 표현 사용 금지).
                        4. 괄호나 특수 기호를 사용한 메타 주석을 포함하지 마세요 (예: "(이건 습관이구나)", "<분석중>" 등).
                        5. 직접적이고 명확하게 답변하세요.
                        6. 모든 응답은 완전한 문장으로 끝내고 적절한 종결어미를 사용하세요.

                        잘못된 응답 예시:
                        "아... '아침 조깅'?! -> (컴퓨터) :-) ... ('But there are many habits like this in the database')"

                        올바른 응답 예시:
                        "아침 조깅은 매일 오전 7시에 시작하는 습관으로 등록되어 있습니다. 이 습관은 2025년 2월 20일에 등록되었습니다."
                        """

        # 응답 형식 지정
        format_instruction = ""
        if format_type == "detailed":
            format_instruction = """상세한 정보를 포함한 응답을 작성하세요. 가능한 모든 관련 정보를 구조적으로 제시하되, 자연스러운 한국어 문장으로 작성하세요."""
        elif format_type == "simple":
            format_instruction = """간결하게 핵심 정보만 전달하는 응답을 작성하세요. 불필요한 세부 사항은 생략하세요."""
        else:  # default
            format_instruction = """명확하고 간결하게 응답하되, 필요한 모든 정보를 포함하세요. 자연스러운 대화체로 작성하세요."""

        # 최종 프롬프트 구성
        prompt = f"""{system_prompt}
                {format_instruction}

                다음은 사용자의 데이터베이스에서 추출한 관련 정보입니다:

                ---
                {combined_context}
                ---

                위 정보를 바탕으로 다음 질문에 답변해주세요. 반드시 자연스러운 한국어로 응답하고, 내부 사고 과정이나 메타 주석을 포함하지 마세요:

                질문: {query}

                답변:"""
        
        return prompt

    @staticmethod
    def create_prompt_with_history(
        query: str, 
        context_items: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]],
        max_history_items: int = 3,
        format_type: Optional[str] = "default"
    ) -> str:
        """
        채팅 기록을 포함한 프롬프트 생성
        
        Args:
            query: 사용자 질문
            context_items: 검색된 컨텍스트 항목 리스트
            chat_history: 채팅 기록 리스트 [{"role": "user"/"assistant", "content": "메시지"}]
            max_history_items: 포함할 최대 대화 기록 수
            format_type: 응답 형식 타입
            
        Returns:
            최종 프롬프트 문자열
        """
        # 기본 프롬프트 생성
        base_prompt = PromptTemplate.create_prompt_from_context(query, context_items, format_type)
        
        # 대화 기록이 없으면 기본 프롬프트 반환
        if not chat_history:
            return base_prompt
        
        # 최근 대화 기록 선택 (최대 max_history_items개)
        recent_history = chat_history[-max_history_items:]
        
        # 대화 기록 포맷팅
        history_text = ""
        for entry in recent_history:
            role = entry.get("role", "")
            content = entry.get("content", "")
            if role == "user":
                history_text += f"사용자: {content}\n"
            elif role == "assistant":
                history_text += f"비서: {content}\n\n"
        
        # 대화 기록을 포함한 프롬프트 구성
        history_prompt = f"""이전 대화 기록:
                        ---
                        {history_text}
                        ---

                        """
        
        # 기존 프롬프트에 대화 기록 삽입
        # "다음은 사용자의 데이터베이스에서..." 부분 앞에 대화 기록 삽입
        parts = base_prompt.split("다음은 사용자의 데이터베이스에서")
        if len(parts) == 2:
            prompt_with_history = parts[0] + history_prompt + "다음은 사용자의 데이터베이스에서" + parts[1]
            return prompt_with_history
        
        return base_prompt