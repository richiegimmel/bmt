from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: Optional[str] = Field(None, max_length=200)


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Schema for paginated chat session list"""
    sessions: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int


class Citation(BaseModel):
    """Schema for document citation"""
    document_id: int
    document_title: str
    chunk_index: int
    page_number: Optional[int] = None
    relevance_score: float


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    session_id: int
    role: str  # 'user' or 'assistant'
    content: str
    citations: Optional[List[Citation]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    """Schema for chat message list"""
    messages: List[ChatMessageResponse]
    total: int


class StreamChunk(BaseModel):
    """Schema for streaming response chunks"""
    type: str  # 'content', 'citation', 'done', 'error'
    content: Optional[str] = None
    citation: Optional[Citation] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for chat request with streaming"""
    session_id: int
    message: str = Field(..., min_length=1)
    stream: bool = Field(default=True)


class DocumentSearchResult(BaseModel):
    """Schema for document search results used in RAG"""
    chunk_id: int
    document_id: int
    document_title: str
    content: str
    page_number: Optional[int] = None
    relevance_score: float
