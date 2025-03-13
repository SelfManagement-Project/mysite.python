from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from db.connection.database import get_db
from services.chat.chat_service import ChatService
import json

router = APIRouter()

# 의존성 주입을 통해 서비스 가져오기 (권장 방식)
def get_chat_service():
    from main import search_service, llm_model
    return ChatService(search_service=search_service, llm_model=llm_model)

# 연결 관리 클래스 (선택적이지만 권장)
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"[Connected] User ID: {user_id}")

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)
        print(f"[Disconnected] User ID: {user_id}")

    async def send_json(self, user_id: int, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/chat/{user_id}/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    chat_id: int = None,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Received] User {user_id}: {data}")

            # JSON 형태로 메시지를 받도록 명확히 처리
            message_data = json.loads(data)
            user_message = message_data.get("message")

            if not user_message:
                await manager.send_json(user_id, {"error": "메시지가 비어 있습니다."})
                continue

            # 채팅 서비스에서 메시지 처리 (DB 세션 전달)
            response = chat_service.process_message(
                message=user_message,
                user_id=user_id,
                chat_id=chat_id,
                db=db  # DB 세션 전달
            )

            # 클라이언트로 응답 전송
            await manager.send_json(user_id, response)

    except WebSocketDisconnect:
        manager.disconnect(user_id)

    except Exception as e:
        error_msg = {"error": f"Chat processing failed: {str(e)}"}
        await manager.send_json(user_id, error_msg)
        await websocket.close()