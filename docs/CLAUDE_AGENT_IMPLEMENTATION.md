# Claude Agent SDK Implementation Guide

## Overview

This document describes the implementation of the Claude Agent SDK with Voyage AI embeddings for the Board Management Tool's Phase 4: AI Chat Interface.

## Implementation Summary

### Key Features Implemented

1. **Voyage AI Embeddings Integration**
   - Using `voyage-law-2` model optimized for legal documents
   - 1024-dimensional vectors for document chunking
   - Separate embedding types for documents and queries
   - Batch processing support (up to 128 texts per batch)

2. **Claude Agent SDK Integration**
   - Claude Sonnet 4.5 for chat responses
   - Streaming responses via Server-Sent Events (SSE)
   - Context-aware conversations with message history
   - Professional legal assistant system prompt

3. **RAG (Retrieval-Augmented Generation)**
   - Semantic search using pgvector
   - Top-5 relevant document chunks retrieved per query
   - Citation tracking with document metadata
   - Relevance scoring with configurable threshold (0.65 for legal docs)

4. **Chat Session Management**
   - Multiple chat sessions per user
   - Persistent message history
   - Session-based conversation context
   - Full CRUD operations for sessions and messages

## Architecture

### Backend Components

#### 1. Embedding Service (`app/services/embedding_service.py`)

**Purpose**: Generate and manage vector embeddings using Voyage AI

**Key Methods**:
- `generate_embedding(text)` - Generate document embeddings
- `generate_query_embedding(query)` - Generate query embeddings
- `generate_embeddings_batch(texts)` - Batch embedding generation
- `search_similar_chunks(query_embedding)` - Vector similarity search
- `store_chunk_with_embedding()` - Store chunks with vectors

**Configuration**:
```python
VOYAGE_API_KEY=your_voyage_api_key
VOYAGE_MODEL=voyage-law-2
```

**Features**:
- Optimized for legal documents with voyage-law-2 model
- Automatic batch processing (128 texts per batch)
- Cosine similarity scoring
- pgvector integration for efficient search

#### 2. Chat Service (`app/services/chat_service.py`)

**Purpose**: Manage chat sessions and AI interactions

**Key Methods**:
- `create_session()` - Create new chat session
- `get_messages()` - Retrieve conversation history
- `retrieve_relevant_documents()` - RAG document retrieval
- `stream_chat_response()` - Stream AI responses with citations
- `generate_non_streaming_response()` - Non-streaming responses

**System Prompt**:
```
You are a professional legal assistant specialized in Kentucky law
and board governance. Your role is to provide accurate, well-researched
legal information based on the documents in your knowledge base.
```

**RAG Process**:
1. User sends message
2. Generate query embedding with Voyage AI
3. Search for top 5 similar document chunks
4. Build context from retrieved documents
5. Send to Claude with conversation history
6. Stream response with citations

#### 3. Chat API Endpoints (`app/api/chat.py`)

**Session Management**:
- `POST /api/v1/chat/sessions` - Create session
- `GET /api/v1/chat/sessions` - List sessions
- `GET /api/v1/chat/sessions/{id}` - Get session
- `DELETE /api/v1/chat/sessions/{id}` - Delete session

**Messaging**:
- `GET /api/v1/chat/sessions/{id}/messages` - Get message history
- `POST /api/v1/chat/sessions/{id}/messages/stream` - Stream response (SSE)
- `POST /api/v1/chat/sessions/{id}/messages` - Non-streaming response

**Streaming Format** (Server-Sent Events):
```json
data: {"type": "citation", "citation": {...}}
data: {"type": "content", "content": "text chunk"}
data: {"type": "done"}
data: {"type": "error", "error": "message"}
```

#### 4. Schemas (`app/schemas/chat.py`)

**Models**:
- `ChatSessionCreate` - Session creation request
- `ChatSessionResponse` - Session data
- `ChatMessageCreate` - Message creation request
- `ChatMessageResponse` - Message data with citations
- `Citation` - Document citation metadata
- `StreamChunk` - Streaming event data

### Frontend Components

#### 1. Chat Types (`frontend/types/chat.ts`)

TypeScript interfaces for:
- ChatSession
- ChatMessage
- Citation
- StreamChunk
- ChatResponse

#### 2. Chat API Client (`frontend/lib/api/chat.ts`)

**Methods**:
- `createSession()` - Create new session
- `listSessions()` - Get all sessions
- `getMessages()` - Get message history
- `sendMessage()` - Send non-streaming message
- `streamMessage()` - Stream response with SSE

**SSE Implementation**:
```typescript
async *streamMessage(sessionId, content, token): AsyncGenerator<StreamChunk>
```

Uses `ReadableStream` API for efficient streaming.

#### 3. Chat UI (`frontend/app/chat/page.tsx`)

**Features**:
- Split-pane layout (sessions sidebar + chat area)
- Real-time message streaming
- Citation display with document links
- Auto-scroll to latest message
- Loading and typing indicators
- Keyboard shortcuts (Enter to send)
- Session management (create, delete, switch)

**Components Used**:
- Button, Input, Card from shadcn/ui
- Lucide icons (Send, Plus, Trash2, FileText, Loader2)
- Toast notifications (sonner)
- Protected route wrapper

## Database Schema

### ChatSession Table
```sql
id: INTEGER PRIMARY KEY
user_id: INTEGER FOREIGN KEY
title: VARCHAR(200)
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

### ChatMessage Table
```sql
id: INTEGER PRIMARY KEY
session_id: INTEGER FOREIGN KEY
role: VARCHAR(20) -- 'user' or 'assistant'
content: TEXT
citations: JSONB -- Array of citation objects
created_at: TIMESTAMP
```

### DocumentChunk Table
```sql
id: INTEGER PRIMARY KEY
document_id: INTEGER FOREIGN KEY
content: TEXT
chunk_index: INTEGER
page_number: INTEGER
embedding: VECTOR(1024) -- pgvector type
created_at: TIMESTAMP
```

## Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Voyage AI
VOYAGE_API_KEY=pa-...
VOYAGE_MODEL=voyage-law-2

# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Dependencies

### Backend (Python)
```
voyageai==0.3.5
anthropic==0.39.0
claude-agent-sdk==0.1.1
fastapi==0.115.5
sqlalchemy==2.0.36
pgvector==0.3.6
sse-starlette==3.0.3
```

### Frontend (TypeScript)
```
next==15.x
react==19.x
lucide-react
sonner
```

## Usage Guide

### 1. Setup

**Install Backend Dependencies**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Configure API Keys**:
Update `backend/.env` with your API keys:
- Get Anthropic API key from https://console.anthropic.com/
- Get Voyage API key from https://www.voyageai.com/

**Run Database Migrations**:
```bash
alembic upgrade head
```

### 2. Start Services

**Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

### 3. Use the Chat Interface

1. Navigate to http://localhost:3000/dashboard
2. Click "Go to Chat"
3. Click "New Chat" to create a session
4. Type your question and press Enter
5. Watch the AI response stream in real-time
6. View citations to source documents

## Key Features

### 1. Document Retrieval (RAG)

When a user asks a question:
1. Message is converted to embedding using Voyage AI
2. pgvector searches for top 5 similar chunks
3. Retrieved chunks are added as context
4. Claude generates response based on context
5. Citations are tracked and displayed

### 2. Streaming Responses

- Uses Server-Sent Events (SSE) for real-time streaming
- Chunks arrive as user reads previous content
- Responsive UX with typing indicators
- Error handling with fallback messages

### 3. Session Management

- Multiple concurrent chat sessions
- Conversation history preserved
- Context maintained across messages
- Easy switching between sessions

### 4. Citations

- Automatic citation extraction
- Links to source documents
- Page number references
- Relevance scores
- Clickable document links (future enhancement)

## Performance Considerations

### Embedding Generation
- Batch processing: 128 documents per API call
- Rate limiting: 100ms delay between batches
- Caching: Embeddings stored in database

### Vector Search
- pgvector cosine distance for fast similarity search
- Indexed vector columns for performance
- Top-k retrieval with configurable limit

### Streaming
- Chunked transfer encoding
- No buffering (X-Accel-Buffering: no)
- Immediate response delivery

## Security

### Authentication
- JWT token required for all endpoints
- User isolation (can only access own sessions)
- Token validation on every request

### Data Privacy
- User messages stored with user_id
- Document access controlled by permissions
- Citations only from accessible documents

## Future Enhancements

### Planned Features
1. **Document Generation**
   - Template-based document creation
   - Legal document formatting
   - Export to PDF/DOCX

2. **Web Search Integration**
   - Kentucky statute lookup
   - Real-time legal research
   - Citation validation

3. **Advanced RAG**
   - Hybrid search (semantic + keyword)
   - Multi-document analysis
   - Citation verification

4. **UI Improvements**
   - Document preview in chat
   - Citation highlighting
   - Export conversation history
   - Markdown rendering

5. **Analytics**
   - Usage tracking
   - Popular queries
   - Document relevance feedback

## Troubleshooting

### Common Issues

**1. Voyage API Error**
```
Error: Invalid API key
```
Solution: Verify `VOYAGE_API_KEY` in `.env`

**2. Streaming Not Working**
```
Error: Response body is null
```
Solution: Check CORS configuration, ensure `Access-Control-Allow-Origin` includes frontend URL

**3. No Documents Retrieved**
```
Empty citations array
```
Solution:
- Verify documents are processed with embeddings
- Check embedding dimension matches (1024)
- Lower `min_score` threshold in search

**4. Slow Response**
```
Long delay before streaming starts
```
Solution:
- Check Voyage API rate limits
- Reduce number of retrieved chunks (limit=3)
- Enable embedding caching

### Debug Mode

Enable debug logging:
```python
# backend/app/services/chat_service.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

### Manual Testing

**1. Test Embedding Generation**:
```bash
cd backend
python -c "
from app.services.embedding_service import EmbeddingService
service = EmbeddingService()
result = service.generate_embedding('test legal text')
print(f'Embedding dimension: {len(result)}')
"
```

**2. Test Chat API**:
```bash
# Create session
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'

# Send message (streaming)
curl -N http://localhost:8000/api/v1/chat/sessions/1/messages/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "What are the board requirements?"}'
```

### Integration Testing

Test the complete workflow:
1. Upload a legal document
2. Process document (generates embeddings)
3. Create chat session
4. Ask question about the document
5. Verify citations appear
6. Check response accuracy

## API Reference

### Complete Endpoint List

**Authentication**:
- `POST /api/v1/auth/login` - Get access token

**Chat Sessions**:
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{id}`
- `DELETE /api/v1/chat/sessions/{id}`

**Chat Messages**:
- `GET /api/v1/chat/sessions/{id}/messages`
- `POST /api/v1/chat/sessions/{id}/messages/stream` (SSE)
- `POST /api/v1/chat/sessions/{id}/messages`

**Documents**:
- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/{id}/process`
- `GET /api/v1/documents/`

## Resources

### Documentation
- [Voyage AI Docs](https://docs.voyageai.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [pgvector Guide](https://github.com/pgvector/pgvector)
- [FastAPI SSE](https://www.starlette.io/responses/#streamingresponse)

### Related Files
- `PROGRESS.md` - Development progress tracker
- `ARCHITECTURE.md` - System architecture
- `NEXT_STEPS.md` - Future development tasks

## Support

For issues or questions:
1. Check this documentation
2. Review error logs in console
3. Verify API keys and configuration
4. Test with simpler queries first
5. Check network connectivity

## Conclusion

The Claude Agent SDK implementation provides a production-ready AI chat interface with:
- ✅ Real-time streaming responses
- ✅ Document retrieval (RAG)
- ✅ Citation tracking
- ✅ Legal-optimized embeddings (voyage-law-2)
- ✅ Session management
- ✅ Professional UI/UX

The system is ready for testing and can be extended with additional features as needed.
