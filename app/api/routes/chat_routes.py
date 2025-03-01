# api/routes/chat_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session
from db.connection.database import get_db
from services.chat.chat_service import ChatService
from services.similarity.search_service import SearchService
from llm.models.deepseek_model import DeepSeekLLM

# 전역 변수로 공유 (실제로는 의존성 주입 사용이 더 좋음)
chat_service = None

class ChatRequest(BaseModel):
    user_id: int
    chat_id: Optional[int] = None
    message: str

router = APIRouter()

@router.post("/send")
def chat_send(request: ChatRequest, db: Session = Depends(get_db)) -> Dict:
    global chat_service
    # print(request)
    try:
        # 최초 호출 시 채팅 서비스 초기화
        if chat_service is None:
            # 여기서는 main.py에서 생성된 서비스를 가져와야 합니다
            # 실제 구현에서는 의존성 주입 방식으로 변경하는 것이 좋습니다
            from main import search_service, llm_model
            chat_service = ChatService(search_service=search_service, llm_model=llm_model)
        
        # 메시지 처리
        response = chat_service.process_message(
            message=request.message,
            user_id=request.user_id,
            chat_id=request.chat_id
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")