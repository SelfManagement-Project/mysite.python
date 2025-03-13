# from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
# from sqlalchemy.sql import func
# from db.connection.database import Base

# class Chat(Base):
#     """
#     채팅 세션 모델
#     """
#     __tablename__ = "chat"
#     __table_args__ = {'extend_existing': True}

#     chat_id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, nullable=False, index=True)
#     session_id = Column(String(100), nullable=True)
#     message = Column(Text, nullable=True)  # 초기 메시지 또는 제목
#     response = Column(Text, nullable=True)  # 초기 응답
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     is_completed = Column(Boolean, default=False)