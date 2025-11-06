from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="New Conversation")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('now()'), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)

    # Message data
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Citations and metadata
    citations = Column(JSON, nullable=True)  # List of document references
    tool_calls = Column(JSON, nullable=True)  # Agent tool usage for debugging

    # Generated documents
    generated_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
