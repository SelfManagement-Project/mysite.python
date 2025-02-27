# # db/models/base.py
# from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from db.connection.database import Base

# # 기존 테이블들의 모델 정의
# class User(Base):
#     __tablename__ = "user"
    
#     id = Column(Integer, primary_key=True, index=True)
#     # 실제 user 테이블에 있는 다른 필드들도 정의
#     # 예: username, email, password_hash 등

# class Document(Base):
#     __tablename__ = "documents"
    
#     id = Column(Integer, primary_key=True, index=True)
#     # 실제 documents 테이블의 필드들 정의

# class Chat(Base):
#     __tablename__ = "chat"
    
#     id = Column(Integer, primary_key=True, index=True)
#     # 실제 chat 테이블의 필드들 정의

# class ChatHistory(Base):
#     __tablename__ = "chat_history"
    
#     id = Column(Integer, primary_key=True, index=True)
#     # 실제 chat_history 테이블의 필드들 정의

# class Schedule(Base):
#     __tablename__ = "schedule"
    
#     id = Column(Integer, primary_key=True, index=True)
#     # 실제 chat_history 테이블의 필드들 정의

# # 필요한 다른 테이블들도 정의