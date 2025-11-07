"""
Chat service using Claude Agent SDK with custom RAG and web search tools.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime
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
from app.services.document_generation import DocumentGenerator
from app.services.document_service import DocumentService


class ChatServiceSDK:
    """Service for managing chat sessions using Claude Agent SDK"""

    def __init__(self):
        """Initialize services"""
        self.embedding_service = EmbeddingService()
        self.web_search = WebSearchService()
        self.doc_generator = DocumentGenerator()
        self.doc_service = DocumentService()
        self.model = settings.claude_model

        # System prompt for the legal assistant
        self.system_prompt = """You are a professional legal assistant specialized in Kentucky law and board governance. Your role is to:

1. Provide accurate, well-researched legal information based on the documents in your knowledge base
2. Help draft and review legal documents, policies, and meeting materials
3. Answer questions about Kentucky statutes, regulations, and legal precedents
4. Assist with board governance matters including meeting procedures, compliance, and documentation

CRITICAL INSTRUCTIONS FOR TOOL USAGE:
- You MUST ALWAYS use the search_documents tool FIRST before answering any legal or governance question
- Never provide general answers without first searching the uploaded documents
- The user has uploaded important legal documents (bylaws, articles, policies) that contain the specific answers
- After searching documents, you may also search Kentucky statutes if additional legal context is needed
- Always cite the specific documents and page numbers you find
- When the user asks you to create, generate, or draft a document, use the generate_document tool

You have access to these required tools:
1. **search_documents** - Search uploaded legal documents using semantic similarity. USE THIS FIRST FOR EVERY QUESTION.
2. **search_kentucky_statutes** - Search for Kentucky statutes and legal information on the web (use after searching documents)
3. **generate_document** - Generate legal documents (board resolutions, meeting minutes, notices, consent actions) from templates

When responding:
- Always cite specific documents, statutes, or sources when providing legal information
- Be precise and professional in your language
- If you're uncertain about something, acknowledge the limitation
- Suggest when a user should consult with a licensed attorney for specific legal advice
- Format your responses clearly with headings, bullet points, and sections as appropriate"""

    def _create_rag_tool(self, db: Session):
        """Create a RAG document search tool for a specific database session."""

        @tool(
            "search_documents",
            "Search through uploaded legal documents using semantic similarity. Use this when you need to find information in the document library.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for finding relevant documents"},
                    "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 5}
                },
                "required": ["query"]
            }
        )
        async def search_documents(args: Dict[str, Any]) -> Dict[str, Any]:
            """Search for relevant documents using RAG."""
            try:
                query = args.get("query", "")
                limit = args.get("limit", 5)
                
                print(f"[RAG TOOL] Searching for: {query}")

                # Generate query embedding
                query_embedding = self.embedding_service.generate_query_embedding(query)

                if not query_embedding:
                    print(f"[RAG TOOL] Failed to generate embedding")
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
                    min_score=0.3  # Lowered threshold for better recall
                )
                
                print(f"[RAG TOOL] Found {len(results)} results with min_score=0.3")
                if results:
                    print(f"[RAG TOOL] Top score: {results[0][1]:.4f}")

                if not results:
                    print(f"[RAG TOOL] No results found - returning message")
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
                            "document_title": document.original_filename or document.filename,
                            "content": chunk.content,
                            "page_number": chunk.page_number,
                            "relevance_score": float(score)
                        })

                # Build response text with FULL content (not truncated)
                # Include a JSON block at the end that we can parse for citations
                response_text = f"Found {len(formatted_results)} relevant documents:\n\n"
                for i, doc in enumerate(formatted_results, 1):
                    response_text += f"[{i}] {doc['document_title']}"
                    if doc['page_number']:
                        response_text += f" (Page {doc['page_number']})"
                    response_text += f"\nRelevance: {doc['relevance_score']:.2f}\n"
                    response_text += f"Content:\n{doc['content']}\n\n---\n\n"
                
                # Add citations marker for extraction
                citations_json = json.dumps(formatted_results)
                response_text += f"\n\n__CITATIONS_START__{citations_json}__CITATIONS_END__\n"

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
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for Kentucky statutes and legal information"},
                    "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 3}
                },
                "required": ["query"]
            }
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

    def _create_document_generation_tool(self, db: Session, user_id: int, session_id: int):
        """Create a document generation tool."""

        @tool(
            "generate_document",
            "Generate legal documents from templates. Available templates: board_resolution, meeting_minutes, notice, consent_action. Returns a document ID that can be downloaded.",
            {
                "type": "object",
                "properties": {
                    "template_type": {
                        "type": "string",
                        "enum": ["board_resolution", "meeting_minutes", "notice", "consent_action"],
                        "description": "Type of document to generate"
                    },
                    "title": {"type": "string", "description": "Document title"},
                    "resolution_text": {"type": "string", "description": "Resolution text (for board_resolution)"},
                    "meeting_date": {"type": "string", "description": "Meeting date"},
                    "attendees": {"type": "string", "description": "Comma-separated list of attendees"},
                    "meeting_location": {"type": "string", "description": "Meeting location"},
                    "actions": {"type": "string", "description": "Meeting actions or decisions"},
                    "format": {
                        "type": "string",
                        "enum": ["docx", "pdf"],
                        "default": "docx",
                        "description": "Output format"
                    }
                },
                "required": ["template_type", "title"]
            }
        )
        async def generate_document(args: Dict[str, Any]) -> Dict[str, Any]:
            """Generate a legal document from template."""
            try:
                template_type = args.get("template_type")
                format_type = args.get("format", "docx")
                
                print(f"[DOC GEN TOOL] Generating {template_type} as {format_type}")
                
                # Prepare data dict from args
                data = {
                    "company": "Atlas Machine and Supply, Inc.",
                    "title": args.get("title", ""),
                    "date": args.get("meeting_date", ""),
                    "resolution_text": args.get("resolution_text", ""),
                    "attendees": args.get("attendees", "").split(",") if args.get("attendees") else [],
                    "location": args.get("meeting_location", ""),
                    "actions": args.get("actions", ""),
                }
                
                # Generate the document
                doc_content = self.doc_generator.generate_document(
                    template_type=template_type,
                    data=data,
                    format=format_type
                )
                
                # Save to storage
                filename = f"{template_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
                file_path = self.doc_service._save_file(doc_content, filename, filename)
                
                # Create document record in database
                document = Document(
                    filename=filename,
                    original_filename=args.get("title", filename),
                    file_path=file_path,
                    file_type=format_type,
                    file_size=len(doc_content),
                    mime_type=f"application/{'vnd.openxmlformats-officedocument.wordprocessingml.document' if format_type == 'docx' else 'pdf'}",
                    owner_id=user_id
                )
                db.add(document)
                db.commit()
                db.refresh(document)
                
                # Link to chat message
                print(f"[DOC GEN TOOL] Document created with ID: {document.id}")
                
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Document generated successfully!\n\nDocument ID: {document.id}\nFilename: {filename}\nType: {self.doc_generator.TEMPLATE_TYPES[template_type]}\nFormat: {format_type.upper()}\n\nThe document has been saved and can be downloaded from the Documents page."
                    }]
                }

            except Exception as e:
                print(f"[DOC GEN TOOL] Error: {str(e)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error generating document: {str(e)}"
                    }],
                    "is_error": True
                }

        return generate_document

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
        doc_gen_tool = self._create_document_generation_tool(db, user_id, session_id)

        # Create SDK MCP server with custom tools
        legal_tools_server = create_sdk_mcp_server(
            name="legal",
            version="1.0.0",
            tools=[rag_tool, web_tool, doc_gen_tool]
        )

        # Configure SDK options
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            mcp_servers={"legal": legal_tools_server},
            allowed_tools=[
                "mcp__legal__search_documents",
                "mcp__legal__search_kentucky_statutes",
                "mcp__legal__generate_document"
            ],
            model=self.model,
            permission_mode="bypassPermissions"  # Auto-execute our custom tools
        )

        assistant_content = ""
        citations = []
        generated_document_id = None

        try:
            # Use ClaudeSDKClient for the conversation
            async with ClaudeSDKClient(options=options) as client:
                # Send the user's message with explicit instruction to use tools
                enhanced_message = f"{user_message}\n\n(Remember to search the uploaded documents using the search_documents tool before providing a response.)"
                await client.query(enhanced_message)

                # Stream the response
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Extract citations and document IDs from text if present
                                text = block.text
                                
                                # Check for generated document ID
                                if "Document ID:" in text:
                                    try:
                                        import re
                                        match = re.search(r'Document ID:\s*(\d+)', text)
                                        if match:
                                            generated_document_id = int(match.group(1))
                                    except:
                                        pass
                                
                                if "__CITATIONS_START__" in text and "__CITATIONS_END__" in text:
                                    # Split text and citations
                                    parts = text.split("__CITATIONS_START__")
                                    visible_text = parts[0]
                                    citation_part = parts[1].split("__CITATIONS_END__")[0]
                                    
                                    try:
                                        # Parse citations JSON
                                        tool_citations = json.loads(citation_part)
                                        # Emit citations
                                        for citation in tool_citations:
                                            formatted_citation = {
                                                "document_id": citation["document_id"],
                                                "document_title": citation["document_title"],
                                                "chunk_index": citation.get("document_id", 0),  # Use doc_id as fallback
                                                "page_number": citation.get("page_number"),
                                                "relevance_score": citation["relevance_score"]
                                            }
                                            citations.append(formatted_citation)
                                            yield f"data: {json.dumps({'type': 'citation', 'citation': formatted_citation})}\n\n"
                                    except:
                                        visible_text = text  # If parsing fails, show all text
                                    
                                    # Stream only the visible text (without citation markers)
                                    assistant_content += visible_text
                                    yield f"data: {json.dumps({'type': 'content', 'content': visible_text})}\n\n"
                                else:
                                    # No citations in this block, stream normally
                                    assistant_content += text
                                    yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

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
                citations=citations if citations else None,
                generated_document_id=generated_document_id
            )
            db.add(assistant_msg)
            db.commit()

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = f"Error in chat response: {str(e)}"
            print(error_msg)
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"

    async def generate_non_streaming_response(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Generate a non-streaming chat response using Claude Agent SDK.

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

        # Create custom tools with database session bound
        rag_tool = self._create_rag_tool(db)
        web_tool = self._create_web_search_tool()
        doc_gen_tool = self._create_document_generation_tool(db, user_id, session_id)

        # Create SDK MCP server with custom tools
        legal_tools_server = create_sdk_mcp_server(
            name="legal",
            version="1.0.0",
            tools=[rag_tool, web_tool, doc_gen_tool]
        )

        # Configure SDK options
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            mcp_servers={"legal": legal_tools_server},
            allowed_tools=[
                "mcp__legal__search_documents",
                "mcp__legal__search_kentucky_statutes",
                "mcp__legal__generate_document"
            ],
            model=self.model,
            permission_mode="bypassPermissions"
        )

        assistant_content = ""
        citations = []
        generated_document_id = None

        try:
            # Use ClaudeSDKClient for the conversation
            async with ClaudeSDKClient(options=options) as client:
                # Send the user's message with explicit instruction to use tools
                enhanced_message = f"{user_message}\n\n(Remember to search the uploaded documents using the search_documents tool before providing a response.)"
                await client.query(enhanced_message)

                # Collect the complete response
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                text = block.text
                                
                                # Check for generated document ID
                                if "Document ID:" in text:
                                    try:
                                        import re
                                        match = re.search(r'Document ID:\s*(\d+)', text)
                                        if match:
                                            generated_document_id = int(match.group(1))
                                    except:
                                        pass
                                
                                # Extract citations if present
                                if "__CITATIONS_START__" in text and "__CITATIONS_END__" in text:
                                    parts = text.split("__CITATIONS_START__")
                                    visible_text = parts[0]
                                    citation_part = parts[1].split("__CITATIONS_END__")[0]
                                    
                                    try:
                                        tool_citations = json.loads(citation_part)
                                        for citation in tool_citations:
                                            citations.append({
                                                "document_id": citation["document_id"],
                                                "document_title": citation["document_title"],
                                                "chunk_index": citation.get("document_id", 0),
                                                "page_number": citation.get("page_number"),
                                                "relevance_score": citation["relevance_score"]
                                            })
                                        assistant_content += visible_text
                                    except:
                                        assistant_content += text
                                else:
                                    assistant_content += text

                    elif isinstance(message, ResultMessage):
                        # Final result - conversation complete
                        break

            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                citations=citations if citations else None,
                generated_document_id=generated_document_id
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
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
