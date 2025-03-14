# services/chat/chat_service.py 수정 버전

from llm.models.deepseek_model import DeepSeekLLM
from llm.prompts.chat_prompt import PromptTemplate
from typing import Dict, Any, Optional, List
from postprocessing.response.response_processor import ResponseProcessor
from postprocessing.formatter.response_formatter import ResponseFormatter
from postprocessing.validation.validation import ResponseValidator
from utils.translation_utils import TranslationService
from sqlalchemy.orm import Session
import time

class ChatService:
    def __init__(self, 
                 search_service,
                 llm_model: Optional[DeepSeekLLM] = None,
                 max_context_items: int = 5,
                 translation_enabled: bool = True):
        """
        챗봇 서비스 초기화
        """
        self.search_service = search_service
        self.llm_model = llm_model if llm_model else DeepSeekLLM()
        self.max_context_items = max_context_items
        self.translation_enabled = translation_enabled
        
        # 사후처리 모듈 초기화
        self.response_processor = ResponseProcessor()
        self.response_formatter = ResponseFormatter()
        self.response_validator = ResponseValidator()
        
        # 번역 서비스 초기화
        if self.translation_enabled:
            self.translation_service = TranslationService(source_lang="ko", target_lang="en")
        
        # 채팅 히스토리 저장소
        self.chat_histories = {}
        
    def process_message(self, 
                        message: str, 
                        user_id: int, 
                        chat_id: Optional[int] = None, 
                        search_threshold: float = 0.1,
                        output_format: str = "default",
                        db: Optional[Session] = None) -> Dict[str, Any]:
        """
        사용자 메시지 처리 및 응답 생성
        
        Args:
            message: 사용자 메시지
            user_id: 사용자 ID
            chat_id: 채팅 ID (선택 사항)
            search_threshold: 검색 임계값
            output_format: 응답 형식
            db: DB 세션 (데이터베이스 저장용)
        """
        start_time = time.time()
        print('test:::::::::::::::::::::::::', chat_id)
        # 채팅 기록 키 생성
        chat_key = f"{user_id}_{chat_id}" if chat_id else f"{user_id}"
        
        # 1. 쿼리 분석 및 검색 기준 설정
        criteria = self._analyze_query_for_criteria(message, user_id)
        
        # 원본 메시지 저장
        original_message = message
        
        # 2. 메시지 번역 (옵션)
        if self.translation_enabled:
            translated_message = self.translation_service.translate_to_target(message)
            print(f"원본 메시지: {message}")
            print(f"번역된 메시지: {translated_message}")
        else:
            translated_message = message
        
        # 3. 벡터 검색 수행 (번역 기능은 search_service 내부에서 처리)
        search_results = self.search_service.search(
            query=message,  # 원본 메시지 전달 (SearchService 내부에서 번역)
            top_k=self.max_context_items, 
            use_cache=True
        )
        
        # 검색 결과 가져오기
        context_items = search_results.get('results', [])
        
        # 4. 채팅 히스토리 가져오기
        chat_history = self.chat_histories.get(chat_key, [])
        
        # 5. 프롬프트 생성 (채팅 기록 포함)
        if len(chat_history) > 0:
            if self.translation_enabled:
                # 번역된 메시지와 컨텍스트로 프롬프트 생성
                prompt = PromptTemplate.create_prompt_with_history(
                    query=translated_message,
                    context_items=context_items,
                    chat_history=chat_history[-3:],  # 최근 3개 대화만 포함
                    format_type=output_format
                )
            else:
                prompt = PromptTemplate.create_prompt_with_history(
                    query=message,
                    context_items=context_items,
                    chat_history=chat_history[-3:],
                    format_type=output_format
                )
        else:
            if self.translation_enabled:
                prompt = PromptTemplate.create_prompt_from_context(
                    query=translated_message,
                    context_items=context_items,
                    format_type=output_format
                )
            else:
                prompt = PromptTemplate.create_prompt_from_context(
                    query=message,
                    context_items=context_items,
                    format_type=output_format
                )
        
        # 6. LLM 응답 생성
        llm_response = self.llm_model.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=256
        )
        
        # 7. 영어 응답을 한국어로 번역 (옵션)
        if self.translation_enabled:
            original_llm_response = llm_response
            llm_response = self.translation_service.translate_to_source(llm_response)
            print(f"원본 응답: {original_llm_response}")
            print(f"번역된 응답: {llm_response}")
        
        # 8. 응답 검증
        is_valid, validation_issues = self.response_validator.validate(
            llm_response, 
            context_items
        )
        
        # 9. 응답이 충분히 유효하지 않으면 다시 생성 시도 (최대 1회)
        if not is_valid and not any("불완전" in issue for issue in validation_issues):
            # 다른 파라미터로 재시도
            retry_response = self.llm_model.generate(
                prompt=prompt,
                temperature=0.05,
                max_tokens=256
            )
            
            # 재시도 응답 번역 (옵션)
            if self.translation_enabled:
                retry_response = self.translation_service.translate_to_source(retry_response)
                
            # 다시 검증
            retry_valid, retry_issues = self.response_validator.validate(retry_response, context_items)
            
            # 재시도가 더 나은 경우 업데이트
            if retry_valid or len(retry_issues) < len(validation_issues):
                llm_response = retry_response
                is_valid = retry_valid
                validation_issues = retry_issues
        
        # 10. 응답 후처리
        processed_response = self.response_processor.process(
            llm_response=llm_response,
            context_items=context_items,
            query=original_message  # 원본 메시지 사용
        )
        
        # 11. 응답 포맷팅
        formatted_response = self.response_formatter.format(
            processed_response=processed_response,
            output_format=output_format
        )
        
        # 최종 응답 텍스트
        final_response = formatted_response.get("formatted_response", llm_response)
        
        # 12. 채팅 기록 업데이트
        chat_history.append({"role": "user", "content": original_message})
        chat_history.append({"role": "assistant", "content": final_response})
        self.chat_histories[chat_key] = chat_history
        
        # 13. 데이터베이스에 저장 (db 세션이 제공된 경우)
        if db:
            from db.connection.database import Chat, ChatHistory
            try:
                # 채팅방 생성 또는 조회
                existing_chat = None

                # 먼저 session_id로 찾기 시도 (같은 세션이면 같은 chat 레코드 사용)
                existing_chat = db.query(Chat).filter(Chat.session_id == chat_key).first()
                
                # 채팅방이 없으면 새로 생성
                if not existing_chat:
                    new_chat = Chat(
                        user_id=user_id,
                        session_id=chat_key,
                        message=original_message,
                        response=final_response,
                        is_completed=False
                    )
                    db.add(new_chat)
                    db.flush()
                    chat_id = new_chat.chat_id
                else:
                    chat_id = existing_chat.chat_id
                
                # 채팅 히스토리에 새 메시지 추가 (항상 실행)
                user_message = ChatHistory(
                    chat_id=chat_id,
                    session_id=chat_key,
                    message_type="user",
                    content=original_message
                )
                db.add(user_message)
                
                assistant_message = ChatHistory(
                    chat_id=chat_id,
                    session_id=chat_key,
                    message_type="assistant",
                    content=final_response
                )
                db.add(assistant_message)
                
                # 커밋
                db.commit()
                
            except Exception as e:
                if db:
                    db.rollback()
                print(f"DB 저장 중 오류 발생: {str(e)}")
        
        # 14. 응답을 임베딩하고 벡터 DB에 저장
        try:
            # 1. 채팅 내용(질문+응답) 저장
            chat_document = f"질문: {original_message}\n답변: {final_response}"
            chat_embedding = self.search_service.embedding_service.generate_embeddings([chat_document])[0]
            
            chat_metadata = {
                'table': 'chat_history',
                'row_id': chat_id, 
                'session_id': chat_key,
                'user_id': user_id,
                'text': chat_document,
                'timestamp': time.time()
            }
            
            # 2. 채팅 세션 정보 저장 (선택적)
            chat_summary = f"사용자 {user_id}의 대화 세션 {chat_id}. 최근 메시지: {original_message}"
            chat_session_embedding = self.search_service.embedding_service.generate_embeddings([chat_summary])[0]
            
            chat_session_metadata = {
                'table': 'chat',
                'row_id': chat_id,
                'session_id': chat_key,
                'user_id': user_id,
                'text': chat_summary,
                'timestamp': time.time()
            }
            
            # 벡터 DB에 저장 (배치 처리)
            self.search_service.vector_store.add_embeddings(
                [chat_embedding, chat_session_embedding], 
                [chat_metadata, chat_session_metadata]
            )
            
            print(f"Chat data indexed in vector DB: chat_id={chat_id}")
            
        except Exception as e:
            print(f"Vector DB 저장 중 오류 발생: {str(e)}")
        
        # 15. 응답 구성
        response = {
            "user_id": user_id,
            "chat_id": chat_id,
            "message": original_message,
            "response": final_response,
            "processing_time": time.time() - start_time,
            "context_items": [item.get('metadata', {}).get('text', '') for item in context_items[:3]],
            "sources": formatted_response.get("sources", []),
            "validation": {
                "is_valid": is_valid,
                "issues": validation_issues if not is_valid else []
            },
            "filtered": formatted_response.get("filtered", False),
            "status": "success"
        }
        
        return response
    
    # _analyze_query_for_criteria 메서드는 그대로 유지
    def _analyze_query_for_criteria(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        쿼리 분석을 통한 검색 기준 생성
        """
        criteria = {}
        
        # 기본 사용자 관련성 설정
        criteria["user_relevance"] = True
        criteria["user_id"] = user_id
        criteria["user_weight"] = 0.8
        
        # 시간 관련 키워드 탐지
        time_keywords = ["언제", "날짜", "기간", "오늘", "내일", "어제", "최근", "일정", "약속"]
        if any(keyword in query for keyword in time_keywords):
            criteria["recency"] = True
            criteria["recency_weight"] = 0.9
            criteria["date_field"] = "created_at"
            
            # 일정 관련 테이블 우선
            criteria["source_priority"] = True
            criteria["priority_sources"] = ["schedule", "habit", "daily_log"]
            criteria["source_weight"] = 0.7
        
        # 개인 습관 관련 키워드 탐지
        habit_keywords = ["습관", "루틴", "매일", "반복", "목표"]
        if any(keyword in query for keyword in habit_keywords):
            criteria["source_priority"] = True
            criteria["priority_sources"] = ["habit", "daily_log", "task"]
            criteria["source_weight"] = 0.8
        
        # 대화/메시지 관련 키워드 탐지
        chat_keywords = ["대화", "메시지", "채팅", "연락", "문자"]
        if any(keyword in query for keyword in chat_keywords):
            criteria["source_priority"] = True
            criteria["priority_sources"] = ["chat", "message", "contact"]
            criteria["source_weight"] = 0.85
            
        return criteria
    
    def clear_chat_history(self, user_id: int, chat_id: Optional[int] = None) -> bool:
        """
        채팅 기록 삭제
        """
        chat_key = f"{user_id}_{chat_id}" if chat_id else f"{user_id}"
        if chat_key in self.chat_histories:
            del self.chat_histories[chat_key]
            return True
        return False