"""
Chat service using Claude Agent SDK with custom RAG and web search tools.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from sqlalchemy.orm import Session
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    SystemMessage
)

from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.embedding_service import EmbeddingService
from app.services.web_search import WebSearchService


class ChatServiceSDK:
    """Service for managing chat sessions using Claude Agent SDK"""

    def __init__(self):
        """Initialize services"""
        self.embedding_service = EmbeddingService()
        self.web_search = WebSearchService()
        self.model = settings.claude_model

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

You have access to custom tools:
1. **search_documents** - Search uploaded legal documents using semantic similarity (RAG)
2. **search_kentucky_statutes** - Search for Kentucky statutes and legal information on the web

Always use these tools when a question relates to specific documents or Kentucky law."""

    def _create_rag_tool(self, db: Session):
        """Create a RAG document search tool for a specific database session."""

        @tool(
            "search_documents",
            "Search through uploaded legal documents using semantic similarity. Use this when you need to find information in the document library.",
            {"query": str, "limit": int}
        )
        async def search_documents(args: Dict[str, Any]) -> Dict[str, Any]:
            """Search for relevant documents using RAG."""
            try:
                query = args.get("query", "")
                limit = args.get("limit", 5)

                # Generate query embedding
                query_embedding = self.embedding_service.generate_query_embedding(query)

                if not query_embedding:
                    return {
                        "content": [{
                            "type": "text",
                            "text": "Failed to generate embedding for query."
                        }],
                        "is_error": True
                    }

                # Search for similar chunks
                results = self.embedding_service.search_similar_chunks(
                    db=db,
                    query_embedding=query_embedding,
                    limit=limit,
                    min_score=0.5
                )

                if not results:
                    return {
                        "content": [{
                            "type": "text",
                            "text": "No relevant documents found in the library."
                        }]
                    }

                # Format results
                formatted_results = []
                for chunk, score in results:
                    document = db.query(Document).filter(
                        Document.id == chunk.document_id
                    ).first()

                    if document:
                        formatted_results.append({
                            "document_id": document.id,
                            "document_title": document.title or document.file_name,
                            "content": chunk.content,
                            "page_number": chunk.page_number,
                            "relevance_score": float(score)
                        })

                # Build response text
                response_text = f"Found {len(formatted_results)} relevant documents:\n\n"
                for i, doc in enumerate(formatted_results, 1):
                    response_text += f"[{i}] {doc['document_title']}"
                    if doc['page_number']:
                        response_text += f" (Page {doc['page_number']})"
                    response_text += f"\nRelevance: {doc['relevance_score']:.2f}\n"
                    response_text += f"Content: {doc['content'][:500]}...\n\n"

                return {
                    "content": [{
                        "type": "text",
                        "text": response_text
                    }]
                }

            except Exception as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error searching documents: {str(e)}"
                    }],
                    "is_error": True
                }

        return search_documents

    def _create_web_search_tool(self):
        """Create a web search tool for Kentucky statutes."""

        @tool(
            "search_kentucky_statutes",
            "Search for Kentucky statutes and legal information on the web. Use this when you need current statute information or legal references not in the uploaded documents.",
            {"query": str, "limit": int}
        )
        async def search_kentucky_statutes(args: Dict[str, Any]) -> Dict[str, Any]:
            """Search for Kentucky statutes on the web."""
            try:
                query = args.get("query", "")
                limit = args.get("limit", 3)

                # Perform web search
                results = await self.web_search.search_kentucky_statutes(query, limit)

                if not results:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"No web results found for: {query}"
                        }]
                    }

                # Format results
                response_text = f"Web Search Results for '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    response_text += f"[{i}] {result['title']}\n"
                    response_text += f"URL: {result['url']}\n"
                    if result.get('snippet'):
                        response_text += f"Summary: {result['snippet']}\n"
                    response_text += "\n"

                response_text += "\nNote: Please verify these web sources and cite URLs when referencing."

                return {
                    "content": [{
                        "type": "text",
                        "text": response_text
                    }]
                }

            except Exception as e:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error in web search: {str(e)}"
                    }],
                    "is_error": True
                }

        return search_kentucky_statutes

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
            Created ChatSession instance
        """
        session = ChatSession(
            user_id=user_id,
            title=title or "New Chat"
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
            limit: Maximum number of records to return

        Returns:
            Tuple of (List of ChatSessions, total count)
        """
        query = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        )

        total = query.count()
        sessions = query.order_by(
            ChatSession.created_at.desc()
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

    async def stream_chat_response(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response using Claude Agent SDK with custom RAG and web search tools.

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

        # Yield control
        await asyncio.sleep(0)

        # Create custom tools with database session bound
        rag_tool = self._create_rag_tool(db)
        web_tool = self._create_web_search_tool()

        # Create SDK MCP server with custom tools
        legal_tools_server = create_sdk_mcp_server(
            name="legal_tools",
            version="1.0.0",
            tools=[rag_tool, web_tool]
        )

        # Configure SDK options
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            mcp_servers={"legal": legal_tools_server},
            allowed_tools=[
                "mcp__legal__search_documents",
                "mcp__legal__search_kentucky_statutes"
            ],
            model=self.model,
            permission_mode="bypassPermissions"  # Auto-execute our custom tools
        )

        assistant_content = ""
        citations = []

        try:
            # Use ClaudeSDKClient for the conversation
            async with ClaudeSDKClient(options=options) as client:
                # Send the user's message
                await client.query(user_message)

                # Stream the response
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Stream text content
                                assistant_content += block.text
                                yield f"data: {json.dumps({'type': 'content', 'delta': block.text})}\n\n"

                            elif isinstance(block, ToolUseBlock):
                                # Tool is being used - could yield status if needed
                                pass

                    elif isinstance(message, ResultMessage):
                        # Final result - conversation complete
                        break

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                citations=citations if citations else None
            )
            db.add(assistant_msg)
            db.commit()

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"Error in chat response: {str(e)}"
            print(error_msg)
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
