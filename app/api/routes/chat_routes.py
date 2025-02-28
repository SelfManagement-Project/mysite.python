from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: int
    chat_id: Optional[int] = None
    message: str

@router.post("/send")
def chat_send(request: ChatRequest) -> Dict:
    try:
        user_message = request.message
        user_id = request.user_id
        chat_id = request.chat_id

        # 챗봇 처리 로직 (임시 응답)
        response_message = f"Received message: {user_message} (Chat ID: {chat_id})"

        print(f"Received: {request}")

        return {
            "status": "success",
            "user_id": user_id,
            "chat_id": chat_id,
            "message": user_message,
            "response": response_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")