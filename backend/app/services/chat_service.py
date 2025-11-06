from typing import List, Dict, Any, Optional, AsyncGenerator
import json
from sqlalchemy.orm import Session
from anthropic import Anthropic
from anthropic.types import MessageStreamEvent

from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.embedding_service import EmbeddingService


class ChatService:
    """Service for managing chat sessions and AI interactions"""

    def __init__(self):
        """Initialize Anthropic client and embedding service"""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.embedding_service = EmbeddingService()

        # System prompt for the legal assistant
        self.system_prompt = """You are a professional legal assistant specialized in Kentucky law and board governance. Your role is to:

1. Provide accurate, well-researched legal information based on the documents in your knowledge base
2. Help draft and review legal documents, policies, and meeting materials
3. Answer questions about Kentucky statutes, regulations, and legal precedents
4. Assist with board governance matters including meeting procedures, compliance, and documentation

When responding:
- Always cite specific documents, statutes, or sources when providing legal information
- Be precise and professional in your language
- If you're uncertain about something, acknowledge the limitation
- Suggest when a user should consult with a licensed attorney for specific legal advice
- Format your responses clearly with headings, bullet points, and sections as appropriate

You have access to a document retrieval tool that allows you to search through uploaded legal documents, policies, and reference materials."""

    def create_session(
        self,
        db: Session,
        user_id: int,
        title: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session

        Args:
            db: Database session
            user_id: User ID
            title: Optional session title

        Returns:
            Created ChatSession
        """
        if not title:
            title = "New Chat"

        session = ChatSession(
            user_id=user_id,
            title=title
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    def get_session(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[ChatSession]:
        """
        Get a chat session by ID

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID

        Returns:
            ChatSession or None if not found
        """
        return db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    def list_sessions(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[ChatSession], int]:
        """
        List chat sessions for a user

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (sessions list, total count)
        """
        query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
        total = query.count()

        sessions = query.order_by(
            ChatSession.updated_at.desc()
        ).offset(skip).limit(limit).all()

        return sessions, total

    def delete_session(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a chat session

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

        if not session:
            return False

        # Delete all messages in the session
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()

        db.delete(session)
        db.commit()

        return True

    def get_messages(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> List[ChatMessage]:
        """
        Get all messages for a chat session

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID

        Returns:
            List of ChatMessages
        """
        # Verify user owns the session
        session = self.get_session(db, session_id, user_id)
        if not session:
            return []

        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def retrieve_relevant_documents(
        self,
        db: Session,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query using RAG

        Args:
            db: Database session
            query: Search query
            limit: Maximum number of chunks to return

        Returns:
            List of relevant document chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_query_embedding(query)

        if not query_embedding:
            return []

        # Search for similar chunks
        results = self.embedding_service.search_similar_chunks(
            db=db,
            query_embedding=query_embedding,
            limit=limit,
            min_score=0.65  # Lower threshold for legal documents
        )

        # Format results with document metadata
        formatted_results = []
        for chunk, score in results:
            # Get document info
            document = db.query(Document).filter(
                Document.id == chunk.document_id
            ).first()

            if document:
                formatted_results.append({
                    "chunk_id": chunk.id,
                    "document_id": document.id,
                    "document_title": document.filename,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "relevance_score": score
                })

        return formatted_results

    async def stream_chat_response(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Claude with RAG

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            user_message: User's message

        Yields:
            Server-Sent Events formatted strings
        """
        # Verify session ownership
        session = self.get_session(db, session_id, user_id)
        if not session:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Session not found'})}\n\n"
            return

        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_documents(db, user_message, limit=5)

        # Build context from retrieved documents
        context = ""
        citations = []

        if relevant_docs:
            context = "\n\n# Relevant Documents\n\n"
            for i, doc in enumerate(relevant_docs, 1):
                context += f"[Document {i}] {doc['document_title']}"
                if doc['page_number']:
                    context += f" (Page {doc['page_number']})"
                context += f"\n{doc['content']}\n\n"

                # Store citation info
                citations.append({
                    "document_id": doc["document_id"],
                    "document_title": doc["document_title"],
                    "chunk_index": doc["chunk_id"],
                    "page_number": doc["page_number"],
                    "relevance_score": doc["relevance_score"]
                })

        # Get message history
        messages = self.get_messages(db, session_id, user_id)

        # Build conversation history
        conversation = []
        for msg in messages[:-1]:  # Exclude the last message (current user message)
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message with context
        current_message = user_message
        if context:
            current_message = f"{context}\n\n# User Question\n{user_message}"

        conversation.append({
            "role": "user",
            "content": current_message
        })

        # Stream response from Claude
        assistant_content = ""

        try:
            # Send citations first
            if citations:
                for citation in citations:
                    yield f"data: {json.dumps({'type': 'citation', 'citation': citation})}\n\n"

            # Stream the AI response
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=conversation
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            chunk = event.delta.text
                            assistant_content += chunk
                            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                citations=citations if citations else None
            )
            db.add(assistant_msg)

            # Update session timestamp
            session.updated_at = assistant_msg.created_at
            db.commit()

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

    async def generate_non_streaming_response(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Generate a non-streaming chat response

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            user_message: User's message

        Returns:
            Dictionary with response and citations
        """
        # Verify session ownership
        session = self.get_session(db, session_id, user_id)
        if not session:
            return {"error": "Session not found"}

        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        db.commit()

        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_documents(db, user_message, limit=5)

        # Build context from retrieved documents
        context = ""
        citations = []

        if relevant_docs:
            context = "\n\n# Relevant Documents\n\n"
            for i, doc in enumerate(relevant_docs, 1):
                context += f"[Document {i}] {doc['document_title']}"
                if doc['page_number']:
                    context += f" (Page {doc['page_number']})"
                context += f"\n{doc['content']}\n\n"

                citations.append({
                    "document_id": doc["document_id"],
                    "document_title": doc["document_title"],
                    "chunk_index": doc["chunk_id"],
                    "page_number": doc["page_number"],
                    "relevance_score": doc["relevance_score"]
                })

        # Get message history
        messages = self.get_messages(db, session_id, user_id)

        # Build conversation history
        conversation = []
        for msg in messages[:-1]:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message with context
        current_message = user_message
        if context:
            current_message = f"{context}\n\n# User Question\n{user_message}"

        conversation.append({
            "role": "user",
            "content": current_message
        })

        # Get response from Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=conversation
            )

            assistant_content = response.content[0].text

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                citations=citations if citations else None
            )
            db.add(assistant_msg)

            # Update session timestamp
            session.updated_at = assistant_msg.created_at
            db.commit()

            return {
                "message": assistant_content,
                "citations": citations
            }

        except Exception as e:
            return {"error": f"Error generating response: {str(e)}"}
