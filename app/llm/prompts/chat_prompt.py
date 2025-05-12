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
        Create a prompt based on retrieved context and user query
        
        Args:
            query: User question (already translated to English)
            context_items: List of retrieved context items
            format_type: Response format type (default, detailed, simple)
            
        Returns:
            Final prompt string
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
            context_texts.append(f"[Source: {table}] {text}")
        
        # 컨텍스트 결합
        combined_context = "\n\n".join(context_texts)
        
        # 영어 프롬프트로 변경
        system_prompt = """You are an intelligent assistant for a personal management platform. You should provide clear and helpful answers based on the user's schedules, habits, conversation history, and other information.

                        When crafting your response, follow these rules:
                        1. Only use the information provided and do not make assumptions about missing information.
                        2. Use natural, complete sentences.
                        3. Do not reveal your internal analysis process (e.g., avoid phrases like "This query is...", "Looking at the information...").
                        4. Do not include meta-annotations in parentheses or special symbols (e.g., "(this is a habit)", "<analyzing>").
                        5. Be direct and clear in your answers.
                        6. End all responses with complete sentences and appropriate concluding words.

                        Incorrect response example:
                        "Ah... 'Morning jogging'?! -> (computer) :-) ... ('But there are many habits like this in the database')"

                        Correct response example:
                        "Morning jogging is registered as a habit that starts at 7 AM daily. This habit was registered on February 20, 2025."
                        """

        # 응답 형식 지정 (영어로 변경)
        format_instruction = ""
        if format_type == "detailed":
            format_instruction = """Provide a detailed response that includes comprehensive information. Present all relevant information in a structured manner, using natural sentences."""
        elif format_type == "simple":
            format_instruction = """Provide a concise response that only conveys essential information. Omit unnecessary details."""
        else:  # default
            format_instruction = """Respond clearly and concisely, but include all necessary information. Use a natural conversational tone."""

        # 최종 프롬프트 구성 (영어로)
        prompt = f"""{system_prompt}
                {format_instruction}

                The following is relevant information extracted from the user's database:

                ---
                {combined_context}
                ---

                Based on the information above, please answer the following question. Respond naturally and do not include your internal thought process or meta-annotations:

                Question: {query}

                Answer:"""
        
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
        Create a prompt that includes chat history
        
        Args:
            query: User question (already translated to English)
            context_items: List of retrieved context items
            chat_history: Chat history list [{"role": "user"/"assistant", "content": "message"}]
            max_history_items: Maximum number of conversation history items to include
            format_type: Response format type
            
        Returns:
            Final prompt string
        """
        # 기본 프롬프트 생성
        base_prompt = PromptTemplate.create_prompt_from_context(query, context_items, format_type)
        
        # 대화 기록이 없으면 기본 프롬프트 반환
        if not chat_history:
            return base_prompt
        
        # 최근 대화 기록 선택 (최대 max_history_items개)
        recent_history = chat_history[-max_history_items:]
        
        # 대화 기록 포맷팅 (영어로 변경)
        history_text = ""
        for entry in recent_history:
            role = entry.get("role", "")
            content = entry.get("content", "")
            
            if role == "user":
                history_text += f"User: {content}\n"
            elif role == "assistant":
                history_text += f"Assistant: {content}\n\n"
        
        # 대화 기록을 포함한 프롬프트 구성
        history_prompt = f"""Previous conversation:
                        ---
                        {history_text}
                        ---

                        """
        
        # 기존 프롬프트에 대화 기록 삽입
        # "The following is relevant information..." 부분 앞에 대화 기록 삽입
        parts = base_prompt.split("The following is relevant information")
        if len(parts) == 2:
            prompt_with_history = parts[0] + history_prompt + "The following is relevant information" + parts[1]
            return prompt_with_history
        
        return base_prompt