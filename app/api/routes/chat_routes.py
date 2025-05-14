from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from db.connection.database import get_db
from services.chat.chat_service import ChatService
import json
import uuid

router = APIRouter()

# 의존성 주입을 통해 서비스 가져오기 (권장 방식)
def get_chat_service():
    from main import search_service, llm_model
    return ChatService(search_service=search_service, llm_model=llm_model)

# 연결 관리 클래스 (멀티 디바이스 지원)
class ConnectionManager:
    def __init__(self):
        # user_id -> {connection_id -> WebSocket}
        self.active_connections: dict[int, dict[str, WebSocket]] = {}
        # connection_id -> (user_id, chat_id)
        self.connection_info: dict[str, tuple[int, int]] = {}

    async def connect(self, user_id: int, chat_id: int, device_id: str, websocket: WebSocket):
        await websocket.accept()
        
        # 사용자별 연결 관리
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            
        # 각 사용자당 여러 연결 가능
        connection_id = f"{user_id}_{chat_id}_{device_id}"
        self.active_connections[user_id][connection_id] = websocket
        self.connection_info[connection_id] = (user_id, chat_id)
        
        print(f"[Connected] User ID: {user_id}, Chat ID: {chat_id}, Device ID: {device_id}")
        print(f"[Active] User {user_id} has {len(self.active_connections[user_id])} active connections")
        
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.connection_info:
            user_id, _ = self.connection_info[connection_id]
            
            if user_id in self.active_connections:
                # 특정 연결만 제거
                self.active_connections[user_id].pop(connection_id, None)
                
                # 사용자의 연결이 모두 없어지면 사용자 키도 제거
                if not self.active_connections[user_id]:
                    self.active_connections.pop(user_id, None)
            
            # 연결 정보 제거
            self.connection_info.pop(connection_id, None)
            print(f"[Disconnected] Connection: {connection_id}")
            
            if user_id in self.active_connections:
                print(f"[Active] User {user_id} has {len(self.active_connections[user_id])} active connections")

    async def send_json_to_connection(self, connection_id: str, message: dict):
        user_id, _ = self.connection_info.get(connection_id, (None, None))
        if user_id and connection_id in self.active_connections.get(user_id, {}):
            websocket = self.active_connections[user_id][connection_id]
            await websocket.send_json(message)
            
    async def broadcast_to_user(self, user_id: int, chat_id: int, message: dict):
        """사용자의 모든 연결에 메시지 브로드캐스트"""
        if user_id in self.active_connections:
            for conn_id, websocket in self.active_connections[user_id].items():
                # 같은 채팅방에 있는 연결에만 메시지 전송
                if self.connection_info.get(conn_id, (None, None))[1] == chat_id:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        print(f"[Error] Broadcasting to {conn_id}: {str(e)}")

manager = ConnectionManager()

@router.websocket("/ws/chat/{user_id}/{chat_id}/{device_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    chat_id: int = None,
    device_id: str = None,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    # device_id가 없으면 자동으로 생성
    if not device_id:
        device_id = str(uuid.uuid4())
        
    # 연결 등록
    connection_id = await manager.connect(user_id, chat_id, device_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Received] User {user_id} ({device_id}): {data}")

            # JSON 형태로 메시지를 받도록 명확히 처리
            message_data = json.loads(data)
            user_message = message_data.get("message")

            if not user_message:
                await manager.send_json_to_connection(connection_id, {"error": "메시지가 비어 있습니다."})
                continue

            # 채팅 서비스에서 메시지 처리 (DB 세션 전달)
            response = chat_service.process_message(
                message=user_message,
                user_id=user_id,
                chat_id=chat_id,
                db=db  # DB 세션 전달
            )

            # 같은 사용자의 모든 연결에 응답 브로드캐스트
            await manager.broadcast_to_user(user_id, chat_id, response)

    except WebSocketDisconnect:
        manager.disconnect(connection_id)

    except Exception as e:
        error_msg = {"error": f"Chat processing failed: {str(e)}"}
        await manager.send_json_to_connection(connection_id, error_msg)
        manager.disconnect(connection_id)
        await websocket.close()