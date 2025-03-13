# # db/models/chat_history.py
# from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
# from sqlalchemy.sql import func
# from db.connection.database import Base

# class ChatHistory(Base):
#     """
#     채팅 메시지 기록 모델
#     """
#     __tablename__ = "chat_history"
#     __table_args__ = {'extend_existing': True}  # 이 옵션을 추가

#     history_id = Column(Integer, primary_key=True, index=True)
#     chat_id = Column(Integer, nullable=False, index=True)
#     session_id = Column(String(100), nullable=True)
#     message_type = Column(String(20), nullable=False)  # 'user' 또는 'assistant'
#     content = Column(Text, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())