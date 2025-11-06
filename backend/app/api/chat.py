from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageListResponse,
)
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    session = chat_service.create_session(
        db=db,
        user_id=current_user.id,
        title=session_data.title
    )
    return session


@router.get("/sessions", response_model=ChatSessionListResponse)
def list_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all chat sessions for the current user"""
    sessions, total = chat_service.list_sessions(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return {
        "sessions": sessions,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit
    }


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    session = chat_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    success = chat_service.delete_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return None


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
def get_chat_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a chat session"""
    messages = chat_service.get_messages(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )

    return {
        "messages": messages,
        "total": len(messages)
    }


@router.post("/sessions/{session_id}/messages/stream")
async def stream_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and stream the AI response using Server-Sent Events (SSE)

    Returns a stream of JSON events:
    - {"type": "citation", "citation": {...}}
    - {"type": "content", "content": "text chunk"}
    - {"type": "done"}
    - {"type": "error", "error": "error message"}
    """
    # Verify session exists and user owns it
    session = chat_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return StreamingResponse(
        chat_service.stream_chat_response(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            user_message=message_data.content
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/sessions/{session_id}/messages", response_model=dict)
async def create_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and get a non-streaming response

    Returns:
    - {"message": "assistant response", "citations": [...]}
    """
    # Verify session exists and user owns it
    session = chat_service.get_session(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    result = await chat_service.generate_non_streaming_response(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        user_message=message_data.content
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )

    return result
