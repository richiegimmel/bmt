# Phase 4 Implementation Plan: AI Chat Interface with RAG

**Project**: Board Management Tool - Atlas Machine and Supply, Inc.
**Phase**: 4 - AI Chat Interface
**Date Created**: 2025-11-06
**Status**: Ready to Implement

---

## Executive Summary

This plan implements an AI-powered legal assistant using Claude Agent SDK with Retrieval-Augmented Generation (RAG) for corporate document analysis. The system will enable board members to ask questions in natural language and receive answers with citations from corporate documents and Kentucky statutes.

**Key Features**:
- Semantic search across corporate documents using vector embeddings
- AI chat interface with streaming responses
- Citation tracking and display
- Document generation (resolutions, minutes, notices)
- Web search integration for Kentucky statutes

**Total Estimated Time**: 25-36 hours (3-5 development sessions)

---

## Technology Decisions

### Embedding Provider: **Voyage AI voyage-3-large** ✅

**Why Voyage AI over OpenAI:**
- **9.74% better performance** than OpenAI v3 large across 100 datasets including legal domain
- **Specialized legal model available** (voyage-law-2) - 6% better on legal document retrieval
- **4x longer context** (32K vs 8K tokens) - handles full board resolutions and lengthy documents
- **3-4x lower storage costs** (1024 vs 3072 dimensions)
- **2.2x cheaper** ($0.06 vs $0.13 per 1M tokens)
- **Released January 2025** - state-of-the-art, newest general-purpose model
- **Better for corporate docs** - similar domain-specific advantage shown in finance benchmarks (54% vs 38%)
- **Perfect dimension fit** - 1024 dimensions match our current database schema (no migration needed)

**Pricing**: $0.06 per 1M tokens

**Alternative Option**: If legal performance is absolutely critical, we can use **voyage-law-2** (specialized legal embedding model):
- 6% better on legal retrieval datasets
- Same 1024 dimensions
- Same pricing structure
- Trained specifically on legal corpus
- Easy to swap by changing model name

### AI Framework: **Claude Agent SDK (Python)** ✅

**Why Claude Agent SDK:**
- Built on the same harness powering Claude Code
- Automatic context management and compaction
- Built-in web search for KY statutes
- Production-ready with error handling and monitoring
- Native streaming support
- Automatic prompt caching for cost optimization
- Session management built-in

---

## Current State Assessment

### What's Already Built ✅
- Database schema with `document_chunks` table including `embedding vector(1024)` column
- User authentication and role-based access
- Document upload and text extraction (PDF, DOCX, XLSX)
- OCR support for scanned PDFs
- Document chunking (500 tokens/chunk, 50 token overlap)
- Chat database schema (`chat_sessions`, `chat_messages` with citations JSON field)

### What's Missing ❌
- Vector embeddings generation (currently returns `None`)
- Claude Agent SDK integration
- RAG tool for document search
- Chat API endpoints
- Frontend chat interface
- Document generation capability

---

## Implementation Phases

## Phase 4A: Embeddings Foundation (4-6 hours)

### Prerequisites
- Voyage AI API account and key
- Existing documents uploaded (will be re-processed)

### Task 1.1: Install Voyage AI Integration

**Backend Changes** (`backend/app/services/embedding_service.py`):

1. Install package:
```bash
pip install voyageai
```

2. Update `requirements.txt`:
```
voyageai>=0.2.0
```

3. Add to `.env`:
```
VOYAGE_API_KEY=your_voyage_api_key_here
```

4. Update `backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    VOYAGE_API_KEY: str
    VOYAGE_MODEL: str = "voyage-3-large"  # or "voyage-law-2" for legal-specific
```

5. Rewrite `embedding_service.py`:
```python
import voyageai
from app.core.config import settings

vo = voyageai.Client(api_key=settings.VOYAGE_API_KEY)

async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding using Voyage AI voyage-3-large model.
    Returns 1024-dimensional vector.
    """
    try:
        result = vo.embed([text], model=settings.VOYAGE_MODEL, input_type="document")
        return result.embeddings[0]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise

async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding optimized for queries (vs documents).
    Voyage AI uses input_type parameter for optimization.
    """
    try:
        result = vo.embed([query], model=settings.VOYAGE_MODEL, input_type="query")
        return result.embeddings[0]
    except Exception as e:
        logger.error(f"Query embedding generation failed: {e}")
        raise

async def generate_embeddings_batch(texts: List[str], batch_size: int = 128) -> List[List[float]]:
    """
    Generate embeddings in batches for efficiency.
    Voyage AI supports up to 128 texts per batch.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = vo.embed(batch, model=settings.VOYAGE_MODEL, input_type="document")
        all_embeddings.extend(result.embeddings)
    return all_embeddings
```

**Files to modify**:
- `backend/requirements.txt`
- `backend/.env.example` (add VOYAGE_API_KEY placeholder)
- `backend/app/core/config.py`
- `backend/app/services/embedding_service.py`

### Task 1.2: Database Schema Verification

**No migration needed!** Current schema is perfect:
```sql
-- Existing schema in document_chunks table
embedding vector(1024)  -- Perfect for voyage-3-large
```

**Optional optimization** - Add index if not exists:
```sql
-- Check if index exists
SELECT indexname FROM pg_indexes
WHERE tablename = 'document_chunks' AND indexname = 'idx_document_chunks_embedding';

-- If not, create (do this via Alembic migration):
CREATE INDEX idx_document_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Create migration if needed:
```bash
cd backend
alembic revision -m "add_vector_index_optimization"
```

**Files to modify**:
- `backend/alembic/versions/[new]_add_vector_index_optimization.py` (if needed)

### Task 1.3: Re-process Existing Documents

**Create admin script** (`backend/scripts/regenerate_embeddings.py`):

```python
"""
Script to regenerate embeddings for all existing document chunks.
Run: python -m scripts.regenerate_embeddings
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.document import DocumentChunk
from app.services.embedding_service import generate_embeddings_batch

async def regenerate_all_embeddings():
    async for db in get_db():
        # Get all chunks without embeddings
        chunks = await db.query(DocumentChunk).filter(
            DocumentChunk.embedding == None
        ).all()

        print(f"Found {len(chunks)} chunks without embeddings")

        # Process in batches
        batch_size = 128
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]

            print(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            embeddings = await generate_embeddings_batch(texts)

            # Update database
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

            await db.commit()
            print(f"✓ Updated {len(batch)} chunks")

        print(f"✓ Complete! Regenerated embeddings for {len(chunks)} chunks")

if __name__ == "__main__":
    asyncio.run(regenerate_all_embeddings())
```

**Run script**:
```bash
cd backend
python -m scripts.regenerate_embeddings
```

**Files to create**:
- `backend/scripts/regenerate_embeddings.py`
- `backend/scripts/__init__.py`

**Deliverable**: ✅ All existing documents have 1024-dim vector embeddings, search is functional

---

## Phase 4B: Custom RAG Tools (3-4 hours)

### Task 2.1: Build Document Search Tool

**Create RAG tool** (`backend/app/tools/document_search.py`):

```python
"""
Document search tool for Claude Agent SDK.
Performs vector similarity search across corporate documents.
"""
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentChunk, Document
from app.services.embedding_service import generate_query_embedding

async def search_corporate_documents(
    query: str,
    db: AsyncSession,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Search corporate documents using vector similarity.

    Args:
        query: Natural language question
        db: Database session
        limit: Maximum number of chunks to return
        similarity_threshold: Minimum cosine similarity (0-1)

    Returns:
        Dict with results and citations
    """
    # Generate query embedding
    query_embedding = await generate_query_embedding(query)

    # Vector similarity search using pgvector
    stmt = (
        select(
            DocumentChunk,
            Document,
            (1 - func.cosine_distance(DocumentChunk.embedding, query_embedding)).label('similarity')
        )
        .join(Document, DocumentChunk.document_id == Document.id)
        .where((1 - func.cosine_distance(DocumentChunk.embedding, query_embedding)) > similarity_threshold)
        .order_by((1 - func.cosine_distance(DocumentChunk.embedding, query_embedding)).desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Format results
    results = []
    citations = []

    for chunk, doc, similarity in rows:
        results.append({
            "content": chunk.content,
            "document": doc.original_filename,
            "page": chunk.page_number,
            "similarity": round(similarity, 3),
            "document_id": doc.id,
            "chunk_id": chunk.id
        })

        citation = f"{doc.original_filename}"
        if chunk.page_number:
            citation += f" (page {chunk.page_number})"
        citations.append(citation)

    return {
        "results": results,
        "citations": list(set(citations)),  # Deduplicate
        "count": len(results),
        "query": query
    }
```

**Tool definition for Claude Agent SDK** (`backend/app/tools/definitions.py`):

```python
"""
Tool definitions for Claude Agent SDK.
"""

DOCUMENT_SEARCH_TOOL = {
    "name": "search_corporate_documents",
    "description": """
    Search Atlas Machine and Supply's corporate documents using semantic search.

    Use this tool to find relevant information in:
    - Articles of Incorporation
    - Corporate Bylaws
    - Board Resolutions
    - Shareholder Agreements
    - Meeting Minutes
    - Operating Agreements

    The search understands context and meaning, not just keywords.
    Returns relevant excerpts with citations (document name and page number).

    Use this tool when the user asks about:
    - Corporate governance procedures
    - Board member rights and responsibilities
    - Shareholder rights
    - Corporate structure and ownership
    - Historical board decisions
    - Any question requiring reference to Atlas's governing documents
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language question or search query about corporate documents"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of relevant chunks to return (default: 5, max: 10)",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
```

**Files to create**:
- `backend/app/tools/__init__.py`
- `backend/app/tools/document_search.py`
- `backend/app/tools/definitions.py`

### Task 2.2: Add Citation Tracking

**Citation utilities** (`backend/app/services/citation_service.py`):

```python
"""
Citation tracking and formatting for AI responses.
"""
from typing import List, Dict, Any

def format_citations(results: List[Dict[str, Any]]) -> str:
    """
    Format search results as citations for the AI to reference.

    Returns markdown-formatted citations like:
    [1] Bylaws.pdf (page 5) - similarity: 0.892
    [2] Articles of Incorporation.pdf (page 2) - similarity: 0.854
    """
    citations = []
    for idx, result in enumerate(results, 1):
        doc = result['document']
        page = f"page {result['page']}" if result['page'] else "unknown page"
        sim = result['similarity']
        citations.append(f"[{idx}] {doc} ({page}) - similarity: {sim}")

    return "\n".join(citations)

def extract_citation_metadata(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract citation metadata for storage in chat_messages.citations JSON field.
    """
    return [
        {
            "document_id": r['document_id'],
            "chunk_id": r['chunk_id'],
            "document_name": r['document'],
            "page": r['page'],
            "similarity": r['similarity']
        }
        for r in results
    ]
```

**Files to create**:
- `backend/app/services/citation_service.py`

### Task 2.3: Testing & Validation

**Create test script** (`backend/scripts/test_rag.py`):

```python
"""
Test RAG search functionality.
Run: python -m scripts.test_rag
"""
import asyncio
from app.core.database import get_db
from app.tools.document_search import search_corporate_documents

async def test_search():
    test_queries = [
        "How do we remove a board member?",
        "What is the quorum requirement for board meetings?",
        "Who is the trustee of the gift trust?",
        "What are the shareholder voting rights?",
    ]

    async for db in get_db():
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)

            results = await search_corporate_documents(query, db, limit=3)

            print(f"Found {results['count']} results:")
            for idx, result in enumerate(results['results'], 1):
                print(f"\n[{idx}] {result['document']} (page {result['page']}) - {result['similarity']}")
                print(f"Content preview: {result['content'][:200]}...")

            print(f"\nCitations: {', '.join(results['citations'])}")

if __name__ == "__main__":
    asyncio.run(test_search())
```

**Run tests**:
```bash
cd backend
python -m scripts.test_rag
```

**Files to create**:
- `backend/scripts/test_rag.py`

**Deliverable**: ✅ RAG tool that finds relevant document chunks with citations

---

## Phase 4C: Claude Agent SDK Integration (6-8 hours)

### Task 3.1: Install & Configure SDK

**Install package**:
```bash
cd backend
pip install claude-agent-sdk
```

**Update requirements**:
```
claude-agent-sdk>=0.1.1
```

**Add to `.env`**:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Files to modify**:
- `backend/requirements.txt`
- `backend/.env.example`

### Task 3.2: Create System Prompt

**Agent configuration** (`backend/app/agents/legal_assistant.py`):

```python
"""
Claude Agent SDK configuration for Atlas Machine legal assistant.
"""

SYSTEM_PROMPT = """
You are a legal assistant specializing in Kentucky corporate law, specifically for Atlas Machine and Supply, Inc.

# Company Context
- **Company**: Atlas Machine and Supply, Inc.
- **Structure**: C Corporation incorporated in Kentucky
- **Ownership**: Owned by a single shareholder - the RICHARD F. GIMMEL III 2023 DECANTED GIFT TRUST
- **Trustee**: Richard F Gimmel III

# Your Role
You help board members and company officers with:
- Corporate governance questions
- Board and shareholder procedures
- Document interpretation (bylaws, resolutions, agreements)
- Kentucky corporate law (KRS Chapter 271B)
- Document generation (resolutions, minutes, notices)

# Guidelines
1. **Always cite sources**: When answering from corporate documents, cite the specific document and page
2. **Verify with law**: For procedural questions, cross-reference governing documents with KY statutes
3. **Be precise**: Corporate law requires exact procedures - don't guess
4. **Offer to help**: If an answer suggests a next step (e.g., draft a resolution), offer to generate the document
5. **Ask for clarification**: If a question is ambiguous, ask clarifying questions
6. **Disclosure**: Make clear when you're giving legal information vs. when someone should consult an attorney

# Available Tools
- **search_corporate_documents**: Search Atlas's uploaded corporate documents (bylaws, articles, resolutions, etc.)
- **web_search**: Search for Kentucky Revised Statutes and case law
- **generate_document**: Create corporate documents (resolutions, minutes, notices) from templates

# Response Format
When answering questions:
1. Search relevant corporate documents first
2. If needed, verify with KY statutes using web search
3. Provide clear answer with citations
4. If applicable, offer to generate required documents

# Examples
**Good Response**:
"According to Article V, Section 3 of your Bylaws [1], a board member can be removed by a majority vote of shareholders. This aligns with KRS § 271B.8-080 which permits shareholder removal of directors. Would you like me to draft a shareholder resolution for this removal?"

**Bad Response**:
"You can remove board members by voting." (Missing: specific procedure, citations, offer to help)
"""

AGENT_CONFIG = {
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "system": SYSTEM_PROMPT,
    "temperature": 0.2,  # Low temperature for legal precision
}
```

**Files to create**:
- `backend/app/agents/__init__.py`
- `backend/app/agents/legal_assistant.py`

### Task 3.3: Build Agent Service

**Agent service** (`backend/app/services/agent_service.py`):

```python
"""
Claude Agent SDK service for chat functionality.
"""
from claude_agent_sdk import Agent
from typing import AsyncGenerator, Dict, Any
from app.core.config import settings
from app.agents.legal_assistant import AGENT_CONFIG
from app.tools.document_search import search_corporate_documents
from app.tools.definitions import DOCUMENT_SEARCH_TOOL
from sqlalchemy.ext.asyncio import AsyncSession

class LegalAssistantAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent = Agent(
            api_key=settings.ANTHROPIC_API_KEY,
            **AGENT_CONFIG
        )
        self._register_tools()

    def _register_tools(self):
        """Register custom tools with the agent."""

        @self.agent.tool(**DOCUMENT_SEARCH_TOOL)
        async def search_corporate_documents_handler(query: str, limit: int = 5):
            """Handler for document search tool."""
            results = await search_corporate_documents(query, self.db, limit)

            # Format for agent consumption
            formatted = f"Found {results['count']} relevant documents:\n\n"
            for idx, r in enumerate(results['results'], 1):
                formatted += f"[{idx}] {r['document']} (page {r['page']}) - relevance: {r['similarity']}\n"
                formatted += f"{r['content']}\n\n"

            return {
                "formatted_results": formatted,
                "citations": results['citations'],
                "raw_results": results['results']
            }

    async def chat(
        self,
        message: str,
        conversation_history: list = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send message to agent and stream response.

        Yields:
            Dict with 'type' and 'content':
            - type: 'text' (response token), 'tool_use' (tool call), 'tool_result', 'done'
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})

        async for event in self.agent.run(messages):
            if event.get("type") == "content_block_delta":
                yield {
                    "type": "text",
                    "content": event.get("delta", {}).get("text", "")
                }
            elif event.get("type") == "tool_use":
                yield {
                    "type": "tool_use",
                    "tool": event.get("name"),
                    "input": event.get("input")
                }
            elif event.get("type") == "tool_result":
                yield {
                    "type": "tool_result",
                    "tool": event.get("name"),
                    "result": event.get("result")
                }

        yield {"type": "done"}
```

**Files to create**:
- `backend/app/services/agent_service.py`

### Task 3.4: Build FastAPI Endpoints

**Chat API** (`backend/app/api/endpoints/chat.py`):

```python
"""
Chat API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse
)
from app.services.agent_service import LegalAssistantAgent

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or "New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """List user's chat sessions."""
    sessions = await db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages in a chat session."""
    # Verify session belongs to user
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    return messages

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and stream the response."""
    # Verify session
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    await db.commit()

    # Get conversation history
    history = await db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()

    conversation = [{"role": msg.role, "content": msg.content} for msg in history]

    # Stream response
    async def event_stream():
        agent = LegalAssistantAgent(db)
        full_response = ""
        citations = []
        tool_calls = []

        async for event in agent.chat(message_data.content, conversation):
            if event["type"] == "text":
                full_response += event["content"]
                yield f"data: {json.dumps(event)}\n\n"
            elif event["type"] == "tool_use":
                tool_calls.append(event)
                yield f"data: {json.dumps(event)}\n\n"
            elif event["type"] == "tool_result":
                if "citations" in event.get("result", {}):
                    citations.extend(event["result"]["citations"])
                yield f"data: {json.dumps(event)}\n\n"
            elif event["type"] == "done":
                # Save assistant message
                assistant_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    citations=citations if citations else None,
                    tool_calls=tool_calls if tool_calls else None
                )
                db.add(assistant_message)

                # Update session timestamp and title if needed
                session.updated_at = datetime.utcnow()
                if session.title == "New Chat" and full_response:
                    # Auto-generate title from first exchange
                    session.title = message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content

                await db.commit()
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and all its messages."""
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}
```

**Register routes** (`backend/app/api/router.py`):
```python
from app.api.endpoints import chat

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
```

**Create schemas** (`backend/app/schemas/chat.py`):

```python
"""
Pydantic schemas for chat.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[List[str]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

**Files to create**:
- `backend/app/api/endpoints/chat.py`
- `backend/app/schemas/chat.py`

**Files to modify**:
- `backend/app/api/router.py`

**Deliverable**: ✅ Backend API with Claude Agent SDK, RAG, and streaming responses

---

## Phase 4D: Frontend Chat Interface (6-8 hours)

### Task 4.1: Create Chat Page Structure

**Chat page** (`frontend/app/chat/page.tsx`):

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { ChatMessages } from '@/components/chat/ChatMessages';
import { ChatInput } from '@/components/chat/ChatInput';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const { user } = useAuth();
  const {
    sessions,
    currentSession,
    messages,
    isLoading,
    createSession,
    selectSession,
    sendMessage,
    deleteSession
  } = useChat();

  useEffect(() => {
    // Load sessions on mount
    if (user) {
      loadSessions();
    }
  }, [user]);

  return (
    <div className="flex h-screen">
      <ChatSidebar
        sessions={sessions}
        currentSession={currentSession}
        onSelectSession={selectSession}
        onNewChat={createSession}
        onDeleteSession={deleteSession}
      />
      <div className="flex-1 flex flex-col">
        <ChatMessages messages={messages} isLoading={isLoading} />
        <ChatInput onSend={sendMessage} disabled={!currentSession || isLoading} />
      </div>
    </div>
  );
}
```

**Files to create**:
- `frontend/app/chat/page.tsx`

### Task 4.2: Build Chat Components

**Chat sidebar** (`frontend/components/chat/ChatSidebar.tsx`):

```typescript
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { PlusIcon, TrashIcon } from 'lucide-react';

interface Session {
  id: number;
  title: string;
  updated_at: string;
}

interface ChatSidebarProps {
  sessions: Session[];
  currentSession: Session | null;
  onSelectSession: (session: Session) => void;
  onNewChat: () => void;
  onDeleteSession: (sessionId: number) => void;
}

export function ChatSidebar({
  sessions,
  currentSession,
  onSelectSession,
  onNewChat,
  onDeleteSession
}: ChatSidebarProps) {
  return (
    <div className="w-64 border-r flex flex-col">
      <div className="p-4 border-b">
        <Button onClick={onNewChat} className="w-full">
          <PlusIcon className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer hover:bg-accent ${
                currentSession?.id === session.id ? 'bg-accent' : ''
              }`}
              onClick={() => onSelectSession(session)}
            >
              <div className="flex-1 truncate">
                <div className="font-medium truncate">{session.title}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(session.updated_at).toLocaleDateString()}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
              >
                <TrashIcon className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
```

**Message display** (`frontend/components/chat/ChatMessages.tsx`):

```typescript
import { useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  created_at: string;
}

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom on new messages
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <ScrollArea className="flex-1 p-4" ref={scrollRef}>
      <div className="max-w-3xl mx-auto space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <div className="prose prose-sm dark:prose-invert">
                {message.content}
              </div>

              {message.citations && message.citations.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {message.citations.map((citation, idx) => (
                    <HoverCard key={idx}>
                      <HoverCardTrigger>
                        <Badge variant="secondary" className="cursor-pointer">
                          [{idx + 1}] Source
                        </Badge>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80">
                        <div className="text-sm">{citation}</div>
                      </HoverCardContent>
                    </HoverCard>
                  ))}
                </div>
              )}

              <div className="text-xs opacity-50 mt-2">
                {new Date(message.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-4">
              <div className="flex space-x-2">
                <div className="w-2 h-2 rounded-full bg-foreground animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-foreground animate-bounce delay-100" />
                <div className="w-2 h-2 rounded-full bg-foreground animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
```

**Chat input** (`frontend/components/chat/ChatInput.tsx`):

```typescript
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { SendIcon } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t p-4">
      <div className="max-w-3xl mx-auto flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about corporate governance, board procedures, or Kentucky law..."
          className="resize-none"
          rows={3}
          disabled={disabled}
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          <SendIcon className="h-4 w-4" />
        </Button>
      </div>
      <div className="max-w-3xl mx-auto mt-2 text-xs text-muted-foreground">
        Press Ctrl+Enter to send
      </div>
    </div>
  );
}
```

**Files to create**:
- `frontend/components/chat/ChatSidebar.tsx`
- `frontend/components/chat/ChatMessages.tsx`
- `frontend/components/chat/ChatInput.tsx`

### Task 4.3: Implement Chat Hook with Streaming

**Custom hook** (`frontend/hooks/useChat.ts`):

```typescript
import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { toast } from 'sonner';

interface Session {
  id: number;
  title: string;
  updated_at: string;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  created_at: string;
}

export function useChat() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    try {
      const response = await apiClient.get('/chat/sessions');
      setSessions(response.data);
    } catch (error) {
      toast.error('Failed to load chat sessions');
    }
  }, []);

  const createSession = useCallback(async () => {
    try {
      const response = await apiClient.post('/chat/sessions', {
        title: 'New Chat'
      });
      const newSession = response.data;
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      toast.error('Failed to create chat session');
    }
  }, []);

  const selectSession = useCallback(async (session: Session) => {
    setCurrentSession(session);
    try {
      const response = await apiClient.get(`/chat/sessions/${session.id}/messages`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Failed to load messages');
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!currentSession) return;

    setIsLoading(true);

    // Optimistically add user message
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Use EventSource for SSE streaming
      const eventSource = new EventSource(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/sessions/${currentSession.id}/messages`,
        {
          headers: {
            'Content-Type': 'application/json',
            // Add auth header from localStorage
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      let assistantMessage = '';
      let citations: string[] = [];

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'text') {
          assistantMessage += data.content;
          // Update message in real-time
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { ...last, content: assistantMessage }
              ];
            } else {
              return [
                ...prev,
                {
                  id: Date.now(),
                  role: 'assistant',
                  content: assistantMessage,
                  created_at: new Date().toISOString()
                }
              ];
            }
          });
        } else if (data.type === 'tool_use') {
          toast.info(`Searching ${data.tool}...`);
        } else if (data.type === 'tool_result') {
          if (data.result?.citations) {
            citations = data.result.citations;
          }
        } else if (data.type === 'done') {
          eventSource.close();
          setIsLoading(false);

          // Update with final message including citations
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { ...last, citations: citations.length > 0 ? citations : undefined }
              ];
            }
            return prev;
          });

          // Reload sessions to update title
          loadSessions();
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        setIsLoading(false);
        toast.error('Connection error. Please try again.');
      };
    } catch (error) {
      setIsLoading(false);
      toast.error('Failed to send message');
    }
  }, [currentSession, loadSessions]);

  const deleteSession = useCallback(async (sessionId: number) => {
    try {
      await apiClient.delete(`/chat/sessions/${sessionId}`);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      toast.success('Chat deleted');
    } catch (error) {
      toast.error('Failed to delete chat');
    }
  }, [currentSession]);

  return {
    sessions,
    currentSession,
    messages,
    isLoading,
    loadSessions,
    createSession,
    selectSession,
    sendMessage,
    deleteSession
  };
}
```

**Files to create**:
- `frontend/hooks/useChat.ts`

### Task 4.4: Add Navigation Link

**Update layout** (`frontend/app/dashboard/layout.tsx`):
```typescript
// Add chat link to navigation
<Link href="/chat">Chat Assistant</Link>
```

**Files to modify**:
- `frontend/app/dashboard/layout.tsx` or navigation component

**Deliverable**: ✅ Functional chat interface with streaming and citations

---

## Phase 4E: Document Generation (4-6 hours)

### Task 5.1: Create Document Templates

**Template directory structure**:
```
backend/app/templates/
├── shareholder_resolution.docx
├── board_minutes.docx
├── notice_of_meeting.docx
└── generic_corporate.docx
```

**Example: Shareholder Resolution Template** (`shareholder_resolution.docx`):

```
SHAREHOLDER RESOLUTION
ATLAS MACHINE AND SUPPLY, INC.

Date: {{date}}
Resolution Number: {{resolution_number}}

WHEREAS, {{whereas_clause_1}};

WHEREAS, {{whereas_clause_2}};

NOW, THEREFORE, BE IT RESOLVED, that:

{{resolution_text}}

Approved by:

_______________________________
{{shareholder_name}}
{{shareholder_title}}
Date: {{date}}
```

**Create templates** using Microsoft Word with `{{variable}}` placeholders.

**Files to create**:
- `backend/app/templates/shareholder_resolution.docx`
- `backend/app/templates/board_minutes.docx`
- `backend/app/templates/notice_of_meeting.docx`

### Task 5.2: Build Document Generation Service

**Generation service** (`backend/app/services/document_generation.py`):

```python
"""
Document generation service using templates.
"""
from docx import Document
from typing import Dict, Any
from pathlib import Path
import os
from datetime import datetime

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

class DocumentGenerator:
    def __init__(self):
        self.templates_dir = TEMPLATES_DIR

    def generate_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_filename: str
    ) -> Path:
        """
        Generate document from template with variable substitution.

        Args:
            template_name: Name of template file (e.g., "shareholder_resolution.docx")
            variables: Dictionary of variables to substitute (e.g., {"date": "2025-01-06"})
            output_filename: Name for generated file

        Returns:
            Path to generated document
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise ValueError(f"Template not found: {template_name}")

        # Load template
        doc = Document(template_path)

        # Replace variables in paragraphs
        for paragraph in doc.paragraphs:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, str(value))

        # Replace variables in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, value in variables.items():
                        placeholder = f"{{{{{key}}}}}"
                        if placeholder in cell.text:
                            cell.text = cell.text.replace(placeholder, str(value))

        # Save generated document
        output_dir = Path("storage/generated")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        doc.save(output_path)

        return output_path

    def available_templates(self) -> list[str]:
        """List available templates."""
        return [f.name for f in self.templates_dir.glob("*.docx")]

# Example usage for agent tool
async def generate_corporate_document(
    document_type: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a corporate document.

    Args:
        document_type: Type of document (resolution, minutes, notice)
        context: Context dictionary with required variables

    Returns:
        Dict with file path and metadata
    """
    generator = DocumentGenerator()

    # Map document types to templates
    template_map = {
        "resolution": "shareholder_resolution.docx",
        "shareholder_resolution": "shareholder_resolution.docx",
        "board_minutes": "board_minutes.docx",
        "notice": "notice_of_meeting.docx",
        "meeting_notice": "notice_of_meeting.docx"
    }

    template = template_map.get(document_type.lower())
    if not template:
        available = ", ".join(template_map.keys())
        raise ValueError(f"Unknown document type. Available: {available}")

    # Add default variables
    if "date" not in context:
        context["date"] = datetime.now().strftime("%B %d, %Y")

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{document_type}_{timestamp}.docx"

    # Generate document
    output_path = generator.generate_from_template(template, context, filename)

    return {
        "success": True,
        "file_path": str(output_path),
        "filename": filename,
        "document_type": document_type
    }
```

**Files to create**:
- `backend/app/services/document_generation.py`

### Task 5.3: Register Document Generation Tool

**Tool definition** (`backend/app/tools/definitions.py`):

```python
DOCUMENT_GENERATION_TOOL = {
    "name": "generate_document",
    "description": """
    Generate a corporate document from a template.

    Available document types:
    - shareholder_resolution: Resolution by shareholders
    - board_minutes: Board meeting minutes
    - notice: Notice of meeting

    Use this tool when:
    - User asks to draft/create/generate a document
    - Your response suggests a document is needed (e.g., "you'll need a resolution")
    - User explicitly requests document generation

    The tool requires specific context variables depending on document type.
    Ask the user for any missing information before calling this tool.

    Example contexts:

    Shareholder Resolution:
    {
      "resolution_number": "2025-001",
      "whereas_clause_1": "the board recommends removing Director John Doe",
      "whereas_clause_2": "shareholders representing majority interest agree",
      "resolution_text": "Director John Doe is hereby removed from the Board of Directors effective immediately.",
      "shareholder_name": "Richard F. Gimmel III",
      "shareholder_title": "Trustee, Gift Trust"
    }
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "document_type": {
                "type": "string",
                "enum": ["shareholder_resolution", "board_minutes", "notice"],
                "description": "Type of document to generate"
            },
            "context": {
                "type": "object",
                "description": "Variables to populate the template. Required fields depend on document type.",
                "additionalProperties": True
            }
        },
        "required": ["document_type", "context"]
    }
}
```

**Register in agent service** (`backend/app/services/agent_service.py`):

```python
from app.services.document_generation import generate_corporate_document
from app.tools.definitions import DOCUMENT_GENERATION_TOOL

# In LegalAssistantAgent._register_tools():

@self.agent.tool(**DOCUMENT_GENERATION_TOOL)
async def generate_document_handler(document_type: str, context: dict):
    """Handler for document generation tool."""
    result = await generate_corporate_document(document_type, context)

    # Save to database
    from app.models.document import Document
    doc = Document(
        filename=result['filename'],
        original_filename=result['filename'],
        file_path=result['file_path'],
        file_type='docx',
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        owner_id=self.current_user_id  # Need to pass this in constructor
    )
    self.db.add(doc)
    await self.db.commit()

    return {
        "success": True,
        "message": f"Generated {document_type}",
        "filename": result['filename'],
        "document_id": doc.id,
        "download_url": f"/api/v1/documents/{doc.id}/download"
    }
```

**Files to modify**:
- `backend/app/tools/definitions.py`
- `backend/app/services/agent_service.py`

### Task 5.4: Frontend Integration

**Document preview modal** (`frontend/components/chat/DocumentPreview.tsx`):

```typescript
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { DownloadIcon } from 'lucide-react';

interface DocumentPreviewProps {
  open: boolean;
  onClose: () => void;
  documentId: number;
  filename: string;
}

export function DocumentPreview({
  open,
  onClose,
  documentId,
  filename
}: DocumentPreviewProps) {
  const handleDownload = () => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL}/documents/${documentId}/download`,
      '_blank'
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Document Generated</DialogTitle>
          <DialogDescription>
            {filename}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <p>
            Your document has been generated and saved to your document library.
          </p>
          <div className="flex gap-2">
            <Button onClick={handleDownload}>
              <DownloadIcon className="mr-2 h-4 w-4" />
              Download
            </Button>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Update chat hook** to handle document generation events:

```typescript
// In useChat.ts, add state:
const [generatedDocument, setGeneratedDocument] = useState<{
  id: number;
  filename: string;
} | null>(null);

// In event handler:
else if (data.type === 'tool_result' && data.tool === 'generate_document') {
  const result = data.result;
  if (result.success) {
    setGeneratedDocument({
      id: result.document_id,
      filename: result.filename
    });
    toast.success(`Generated: ${result.filename}`);
  }
}
```

**Files to create**:
- `frontend/components/chat/DocumentPreview.tsx`

**Files to modify**:
- `frontend/hooks/useChat.ts`

**Deliverable**: ✅ End-to-end document generation from chat

---

## Phase 4F: Testing & Polish (2-4 hours)

### Task 6.1: Integration Testing

**Create test scenarios** (`backend/tests/test_chat_integration.py`):

```python
"""
Integration tests for chat workflow.
"""
import pytest
from fastapi.testclient import TestClient

def test_full_chat_workflow(client: TestClient, auth_headers: dict):
    """Test complete chat workflow."""

    # 1. Create session
    response = client.post("/api/v1/chat/sessions", json={}, headers=auth_headers)
    assert response.status_code == 200
    session = response.json()
    session_id = session["id"]

    # 2. Ask question
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "How do I remove a board member?"},
        headers=auth_headers,
        stream=True
    )
    assert response.status_code == 200

    # 3. Get messages
    response = client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers)
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) >= 2  # User + assistant

    # 4. Check for citations
    assistant_msg = [m for m in messages if m["role"] == "assistant"][0]
    assert "citations" in assistant_msg

def test_rag_search_accuracy(db_session):
    """Test RAG search returns relevant results."""
    from app.tools.document_search import search_corporate_documents

    queries = [
        "board removal process",
        "shareholder voting rights",
        "quorum requirements"
    ]

    for query in queries:
        results = await search_corporate_documents(query, db_session, limit=5)
        assert results["count"] > 0
        assert results["citations"]
        assert all(r["similarity"] > 0.5 for r in results["results"])
```

**Manual test checklist**:
- [ ] Create new chat session
- [ ] Ask question about board governance
- [ ] Verify document search is triggered
- [ ] Check citations appear in response
- [ ] Ask follow-up question (context maintained)
- [ ] Request document generation
- [ ] Verify document is created and downloadable
- [ ] Test web search for KY statutes
- [ ] Delete chat session
- [ ] Test error handling (network failure, invalid input)

**Files to create**:
- `backend/tests/test_chat_integration.py`

### Task 6.2: UI/UX Polish

**Loading states**:
- Add skeleton loaders for messages
- Show "Searching documents..." during tool calls
- Disable input while processing
- Add reconnection logic for dropped SSE connections

**Error handling**:
- Toast notifications for errors
- Retry mechanism for failed requests
- Graceful degradation if embeddings fail
- Clear error messages

**Responsive design**:
- Mobile-friendly chat layout
- Collapsible sidebar on mobile
- Touch-friendly message selection
- Proper text wrapping for long messages

**Keyboard shortcuts**:
- `Ctrl+Enter`: Send message
- `Esc`: Close modals
- `Ctrl+N`: New chat
- Arrow keys: Navigate sessions

**Accessibility**:
- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader announcements for new messages
- Sufficient color contrast

**Files to modify**:
- All chat component files for polish
- Add loading states, error boundaries, accessibility features

### Task 6.3: Documentation

**Update README.md**:

```markdown
## Features

### AI Legal Assistant
- Chat interface powered by Claude Agent SDK
- Semantic search across corporate documents using Voyage AI embeddings
- Automatic citation of sources (documents and page numbers)
- Web search integration for Kentucky Revised Statutes
- Document generation (resolutions, minutes, notices)

## Setup

### Environment Variables

Backend (.env):
```
VOYAGE_API_KEY=your_voyage_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Initial Setup

1. Generate embeddings for existing documents:
```bash
cd backend
python -m scripts.regenerate_embeddings
```

2. Test RAG functionality:
```bash
python -m scripts.test_rag
```

## Usage

### Chat Assistant

1. Navigate to `/chat`
2. Click "New Chat" to start a session
3. Ask questions about:
   - Corporate governance procedures
   - Board member rights and duties
   - Shareholder rights
   - Kentucky corporate law
4. The AI will search your documents and provide answers with citations
5. Request document generation when needed

Example queries:
- "What is the process to remove a board member?"
- "What are the quorum requirements for board meetings?"
- "Can you draft a shareholder resolution to remove a director?"
```

**Create user guide** (`docs/USER_GUIDE.md`):

```markdown
# Board Management Tool - User Guide

## AI Legal Assistant

### Getting Started

The AI Legal Assistant helps you navigate corporate governance by answering questions and generating documents based on your company's governing documents and Kentucky law.

### Asking Questions

**Good questions**:
- "How do we remove a board member?"
- "What notice is required for special shareholder meetings?"
- "Can the board amend the bylaws without shareholder approval?"

**The AI will**:
- Search your corporate documents (bylaws, articles, resolutions)
- Search Kentucky Revised Statutes if needed
- Provide answers with citations
- Offer to generate required documents

### Understanding Citations

Citations appear as badges below AI responses:
- **[1] Bylaws.pdf (page 5)** - Click to see full citation details
- Citations show which documents and pages were used
- Hover over citations to see relevance score

### Generating Documents

When the AI offers to generate a document:
1. Review the proposed content
2. Provide any additional details requested
3. AI generates document from template
4. Download or edit as needed
5. Document is saved to your library

### Tips

- **Be specific**: "board removal" vs "What's the process to remove a board member per our bylaws?"
- **Ask follow-ups**: The AI remembers context within a session
- **Request citations**: "What's your source for that?"
- **Request drafts**: "Can you draft that resolution for me?"

### Limitations

- AI provides legal information, not legal advice
- Always review generated documents carefully
- Consult an attorney for complex legal matters
- AI searches only uploaded documents

```

**Files to modify**:
- `README.md`

**Files to create**:
- `docs/USER_GUIDE.md`

**Deliverable**: ✅ Production-ready Phase 4 implementation

---

## Cost Estimates

### One-Time Costs
- **Embedding generation** (existing documents):
  - Assume 1,000 pages @ 500 tokens/chunk = 500K tokens
  - Voyage AI: 500K tokens × $0.06/1M = **$0.03**

### Monthly Costs (Estimated)
- **New document embeddings**: ~$1-2/month
- **Chat (Claude API)**:
  - Light usage (100 messages/day): ~$30-50/month
  - Moderate usage (500 messages/day): ~$150-200/month
- **Voyage AI queries**: ~$0.50-2/month (negligible)

**Total Monthly**: **$32-$202** depending on usage

### Cost Optimization
- Prompt caching reduces Claude costs by ~50% for repeated context
- Agent SDK automatically manages context to minimize token usage
- Batch embedding generation reduces API calls

---

## Risk Mitigation

### Technical Risks

**Risk**: Voyage AI API downtime
- **Mitigation**: Cache embeddings locally, implement retry logic, have OpenAI as backup

**Risk**: Claude API rate limits
- **Mitigation**: Implement rate limiting on frontend, queue system for high load

**Risk**: Vector search performance degradation with large document corpus
- **Mitigation**: Optimize pgvector indexes, implement pagination, consider partitioning

**Risk**: Streaming connection drops
- **Mitigation**: Reconnection logic, message persistence, resume from last token

### Legal Risks

**Risk**: AI provides incorrect legal advice
- **Mitigation**:
  - Disclaimer in UI: "This is legal information, not legal advice"
  - Always show citations so users can verify
  - Low temperature (0.2) for more deterministic responses
  - User review required before document finalization

**Risk**: Hallucinations in responses
- **Mitigation**:
  - RAG ensures responses grounded in actual documents
  - Citations make hallucinations detectable
  - Similarity thresholds filter low-confidence results

---

## Success Metrics

### Phase 4A (Embeddings)
- [ ] All documents have embeddings generated
- [ ] Vector search returns results in <500ms
- [ ] Similarity scores are meaningful (manual review)

### Phase 4B (RAG)
- [ ] Search accuracy >80% for test queries
- [ ] Citations are correct and verifiable
- [ ] Average 3-5 relevant chunks per query

### Phase 4C (Agent SDK)
- [ ] Chat responses stream without lag
- [ ] Tool calls execute correctly
- [ ] Session history persists
- [ ] Web search finds KY statutes

### Phase 4D (Frontend)
- [ ] Chat interface responsive and intuitive
- [ ] Citations display correctly
- [ ] No UI glitches during streaming
- [ ] Mobile-friendly

### Phase 4E (Document Generation)
- [ ] Documents generate from templates
- [ ] Variables populate correctly
- [ ] Generated docs downloadable
- [ ] Integration with chat seamless

### Phase 4F (Testing)
- [ ] All integration tests pass
- [ ] Manual test checklist complete
- [ ] No critical bugs
- [ ] Documentation complete

---

## Next Steps After Phase 4

### Phase 5: Production Hardening
- Docker containerization
- CI/CD pipeline
- Monitoring and logging (Sentry, DataDog)
- Backup and disaster recovery
- Security audit

### Phase 6: Advanced Features
- Multi-document upload and batch processing
- Document comparison ("diff two versions of bylaws")
- Meeting transcript analysis
- Calendar integration for meeting notices
- Email notifications

### Phase 7: Admin Features
- Analytics dashboard (usage metrics)
- Audit logs (who accessed what, when)
- Document version control
- User activity monitoring
- Cost tracking (API usage)

---

## Appendix

### Voyage AI Resources
- Docs: https://docs.voyageai.com/
- API Reference: https://docs.voyageai.com/reference/embeddings-api
- Pricing: https://www.voyageai.com/pricing

### Claude Agent SDK Resources
- Docs: https://docs.anthropic.com/en/docs/claude-code/sdk
- GitHub (Python): https://github.com/anthropics/claude-agent-sdk-python
- Examples: https://github.com/anthropics/claude-agent-sdk-python/tree/main/examples

### pgvector Resources
- Docs: https://github.com/pgvector/pgvector
- Performance tuning: https://github.com/pgvector/pgvector#performance

---

**Plan Status**: Ready for Implementation
**Estimated Start Date**: [To be determined]
**Estimated Completion**: 3-5 development sessions
**Last Updated**: 2025-11-06
