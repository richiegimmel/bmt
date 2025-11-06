# Board Management Tool - System Architecture

## Overview

The Board Management Tool is a full-stack web application built with a modern tech stack, featuring document management, vector search, and AI-powered legal assistance capabilities.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Next.js 15 Frontend (React + TypeScript)            │   │
│  │  - Pages (Login, Dashboard, Documents, Chat)         │   │
│  │  - Components (ShadCN UI)                            │   │
│  │  - Context (Auth, State Management)                  │   │
│  │  - API Client (fetch wrapper)                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/S + JSON
                              │ JWT Authentication
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend (Python)                            │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ API Routes                                      │  │   │
│  │  │ - /auth  (login, register, refresh)            │  │   │
│  │  │ - /users (CRUD, admin only)                    │  │   │
│  │  │ - /documents (upload, list, download)          │  │   │
│  │  │ - /chat (sessions, messages, stream)           │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Services                                        │  │   │
│  │  │ - Authentication (JWT, bcrypt)                 │  │   │
│  │  │ - Document Processing (text extraction)        │  │   │
│  │  │ - Embedding Generation (Claude API)            │  │   │
│  │  │ - Vector Search (pgvector)                     │  │   │
│  │  │ - Agent Orchestration (Claude Agent SDK)       │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy ORM
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL 16 + pgvector                            │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │ Tables                                          │  │   │
│  │  │ - users (auth, roles)                          │  │   │
│  │  │ - documents (metadata)                         │  │   │
│  │  │ - document_chunks (text + embeddings)          │  │   │
│  │  │ - chat_sessions (conversations)                │  │   │
│  │  │ - chat_messages (with citations)               │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Filesystem (ZFS-backed)                       │   │
│  │  - /storage/ (permanent documents)                   │   │
│  │  - /uploads/ (temporary upload staging)              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    External Services                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Anthropic Claude API                                │   │
│  │  - Text Generation (Agent SDK)                       │   │
│  │  - Embeddings (1024-dim vectors)                     │   │
│  │  - Model: claude-sonnet-4-5-20250929                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 15 | React framework with App Router |
| Language | TypeScript | 5.x | Type-safe JavaScript |
| Styling | Tailwind CSS | v4 | Utility-first CSS |
| UI Library | ShadCN UI | Latest | Pre-built React components |
| Icons | Lucide Icons | Latest | Icon library |
| Forms | React Hook Form | Latest | Form validation |
| Notifications | Sonner | Latest | Toast notifications |
| HTTP Client | fetch API | Native | API requests |

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.115.5 | Modern Python web framework |
| Language | Python | 3.12 | Backend language |
| ORM | SQLAlchemy | 2.0.36 | Database ORM |
| Migrations | Alembic | 1.14.0 | Database schema migrations |
| Auth | python-jose | 3.3.0 | JWT token handling |
| Password | bcrypt | 4.2.1 | Password hashing |
| Validation | Pydantic | 2.10.3 | Data validation |
| Server | Uvicorn | 0.32.1 | ASGI server |

### Database

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Database | PostgreSQL | 16 | Primary data store |
| Extension | pgvector | 0.8.0 | Vector similarity search |
| Vector Dim | 1024 | - | Claude embedding size |

### AI/ML

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| SDK | claude-agent-sdk | 0.1.1 | Agent orchestration |
| API Client | anthropic | 0.39.0 | Claude API access |
| Tokenizer | tiktoken | 0.8.0 | Token counting |
| Model | claude-sonnet-4 | - | AI model |

### Document Processing

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| PDF | PyPDF2 | 3.0.1 | PDF text extraction |
| Word | python-docx | 1.1.2 | DOCX text extraction |
| Excel | openpyxl | 3.1.5 | XLSX text extraction |

---

## Data Model

### Entity Relationship Diagram

```
┌──────────────────┐
│     users        │
├──────────────────┤
│ id (PK)          │
│ email            │◄──────┐
│ username         │       │
│ hashed_password  │       │
│ full_name        │       │
│ is_active        │       │
│ is_admin         │       │
│ created_at       │       │
│ updated_at       │       │
└──────────────────┘       │
        │                  │
        │ owns             │ owns
        │                  │
        ▼                  │
┌──────────────────┐       │
│   documents      │       │
├──────────────────┤       │
│ id (PK)          │       │
│ filename         │       │
│ original_filename│       │
│ file_path        │       │
│ file_type        │       │
│ file_size        │       │
│ mime_type        │       │
│ extracted_text   │       │
│ summary          │       │
│ folder           │       │
│ owner_id (FK)    │───────┘
│ created_at       │
│ updated_at       │
└──────────────────┘
        │
        │ has many
        │
        ▼
┌──────────────────┐
│ document_chunks  │
├──────────────────┤
│ id (PK)          │
│ document_id (FK) │
│ content          │
│ chunk_index      │
│ embedding        │◄──── vector(1024) type
│ page_number      │
│ created_at       │
└──────────────────┘

┌──────────────────┐
│  chat_sessions   │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │───────┐
│ title            │       │
│ created_at       │       │
│ updated_at       │       │
└──────────────────┘       │
        │                  │
        │ has many         │ belongs to
        │                  │
        ▼                  │
┌──────────────────┐       │
│  chat_messages   │       │
├──────────────────┤       │
│ id (PK)          │       │
│ session_id (FK)  │       │
│ role             │       │
│ content          │       │
│ citations (JSON) │       │
│ tool_calls (JSON)│       │
│ generated_doc_id │       │
│ created_at       │       │
└──────────────────┘       │
                           │
                    ┌──────────────┐
                    │    users     │
                    └──────────────┘
```

### Table Schemas

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### documents
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR NOT NULL,
    extracted_text TEXT,
    summary TEXT,
    folder VARCHAR DEFAULT '/',
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### document_chunks
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1024),  -- pgvector type
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

#### chat_sessions
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### chat_messages
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    citations JSON,  -- [{doc_id, chunk_id, page, snippet}]
    tool_calls JSON,  -- Agent tool usage for debugging
    generated_document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## API Architecture

### Authentication Flow

```
┌──────────┐                                     ┌──────────┐
│  Client  │                                     │  Server  │
└─────┬────┘                                     └─────┬────┘
      │                                                │
      │  POST /auth/register                          │
      │  {email, username, password}                  │
      ├──────────────────────────────────────────────►│
      │                                                │
      │  201 Created                                  │
      │  {id, email, username, ...}                   │
      │◄──────────────────────────────────────────────┤
      │                                                │
      │  POST /auth/login                             │
      │  {username, password}                         │
      ├──────────────────────────────────────────────►│
      │                                                │
      │  200 OK                                       │
      │  {access_token, refresh_token, token_type}    │
      │◄──────────────────────────────────────────────┤
      │                                                │
      │  Store tokens in localStorage                 │
      │                                                │
      │  GET /auth/me                                 │
      │  Authorization: Bearer <access_token>         │
      ├──────────────────────────────────────────────►│
      │                                                │
      │  200 OK                                       │
      │  {id, email, username, is_admin, ...}         │
      │◄──────────────────────────────────────────────┤
      │                                                │
      │  (access_token expires after 30 min)          │
      │                                                │
      │  POST /auth/refresh                           │
      │  {refresh_token}                              │
      ├──────────────────────────────────────────────►│
      │                                                │
      │  200 OK                                       │
      │  {access_token, refresh_token, token_type}    │
      │◄──────────────────────────────────────────────┤
```

### Document Processing Flow

```
┌──────────┐                                     ┌──────────┐
│  Client  │                                     │  Server  │
└─────┬────┘                                     └─────┬────┘
      │                                                │
      │  POST /documents/upload                       │
      │  multipart/form-data: file                    │
      ├──────────────────────────────────────────────►│
      │                                                │
      │                                          ┌─────┴─────┐
      │                                          │ 1. Validate│
      │                                          │    file    │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 2. Save to │
      │                                          │    disk    │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 3. Create  │
      │                                          │   DB record│
      │                                          └─────┬─────┘
      │  201 Created                                  │
      │  {id, filename, file_type, ...}               │
      │◄──────────────────────────────────────────────┤
      │                                                │
      │  POST /documents/{id}/process                 │
      ├──────────────────────────────────────────────►│
      │                                                │
      │                                          ┌─────┴─────┐
      │                                          │ 1. Extract │
      │                                          │    text    │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 2. Chunk   │
      │                                          │    text    │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 3. Generate│
      │                                          │  embeddings│
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 4. Store in│
      │                                          │    pgvector│
      │                                          └─────┬─────┘
      │  200 OK                                       │
      │  {status: "processed", chunks: 42}            │
      │◄──────────────────────────────────────────────┤
```

### Chat RAG Flow

```
┌──────────┐                                     ┌──────────┐
│  Client  │                                     │  Server  │
└─────┬────┘                                     └─────┬────┘
      │                                                │
      │  POST /chat/sessions                          │
      ├──────────────────────────────────────────────►│
      │  201 Created {id, title}                      │
      │◄──────────────────────────────────────────────┤
      │                                                │
      │  POST /chat/stream                            │
      │  {session_id, message: "What is..."}          │
      ├──────────────────────────────────────────────►│
      │                                                │
      │                                          ┌─────┴─────┐
      │                                          │ 1. Generate│
      │                                          │  query emb │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 2. Search  │
      │                                          │   pgvector │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 3. Retrieve│
      │                                          │   top docs │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 4. Build   │
      │                                          │   context  │
      │                                          └─────┬─────┘
      │                                          ┌─────┴─────┐
      │                                          │ 5. Call    │
      │                                          │   Claude   │
      │                                          └─────┬─────┘
      │  SSE: data: {"type": "text", "data": "..."}   │
      │◄──────────────────────────────────────────────┤
      │  SSE: data: {"type": "citation", "doc_id": 5} │
      │◄──────────────────────────────────────────────┤
      │  SSE: data: {"type": "text", "data": "..."}   │
      │◄──────────────────────────────────────────────┤
      │  SSE: data: {"type": "done"}                  │
      │◄──────────────────────────────────────────────┤
```

---

## Security Architecture

### Authentication & Authorization

1. **JWT Tokens**
   - Access Token: 30-minute expiry
   - Refresh Token: 7-day expiry
   - Stored in localStorage (client-side)
   - HS256 algorithm with SECRET_KEY

2. **Password Security**
   - bcrypt hashing with salt
   - Minimum 8 characters
   - No plain-text storage

3. **Role-Based Access Control**
   - Two roles: User, Admin
   - Admin: Full user management access
   - User: Access to own documents and chat

4. **API Protection**
   - All endpoints require authentication (except /auth/login, /auth/register)
   - HTTPBearer scheme
   - Token validation on every request

### CORS Configuration

```python
# backend/.env
CORS_ORIGINS=["http://localhost:3000","http://10.0.2.134:3000"]
```

- Restricts API access to approved origins
- Allows credentials (cookies/auth headers)
- All methods and headers allowed (dev mode)
- Should be restricted in production

---

## File Storage Strategy

### Directory Structure

```
backend/
├── storage/                    # Permanent document storage
│   ├── 2025/                  # Year-based organization
│   │   ├── 01/               # Month
│   │   │   └── uuid_filename.pdf
│   │   └── 02/
│   └── ...
└── uploads/                   # Temporary upload staging
    └── temp_uploads.tmp       # Cleared periodically
```

### File Naming Convention

```python
# Format: {uuid}_{safe_filename}.{ext}
# Example: 7f3b2a1c-4d5e-6f7g-8h9i-0j1k2l3m4n5o_meeting_minutes.pdf

import uuid
import os
from datetime import datetime

def generate_file_path(original_filename: str) -> str:
    """Generate unique file path"""
    ext = os.path.splitext(original_filename)[1]
    unique_id = str(uuid.uuid4())
    safe_name = secure_filename(original_filename)

    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    filename = f"{unique_id}_{safe_name}"
    path = f"storage/{year}/{month}/{filename}"

    return path
```

---

## Deployment Architecture (Future)

### Production Recommendations

```
┌─────────────────────────────────────────────────────┐
│                    Load Balancer                      │
│                 (nginx / Caddy)                       │
└────────┬──────────────────────────────────┬─────────┘
         │                                  │
         │ HTTPS                            │ HTTPS
         ▼                                  ▼
┌────────────────────┐           ┌────────────────────┐
│  Frontend Server   │           │  Backend Server    │
│   (Next.js SSR)    │           │   (FastAPI)        │
│   Port: 3000       │           │   Port: 8000       │
└────────────────────┘           └────────┬───────────┘
                                          │
                                          │ PostgreSQL
                                          ▼
                                 ┌────────────────────┐
                                 │   PostgreSQL 16    │
                                 │   + pgvector       │
                                 └────────────────────┘
                                          │
                                          │ ZFS
                                          ▼
                                 ┌────────────────────┐
                                 │   File Storage     │
                                 │   (ZFS Pool)       │
                                 └────────────────────┘
```

### Environment Considerations

1. **Development**
   - Hot reload enabled
   - Debug mode on
   - Permissive CORS
   - SQLite or local PostgreSQL

2. **Production**
   - Build optimizations
   - Debug mode off
   - Strict CORS
   - Connection pooling
   - Rate limiting
   - Logging/monitoring

---

## Performance Considerations

### Database Optimization

1. **Indexes**
   ```sql
   -- Already created
   CREATE INDEX ON users(email);
   CREATE INDEX ON users(username);
   CREATE INDEX ON documents(owner_id);
   CREATE INDEX ON document_chunks(document_id);

   -- Vector similarity index
   CREATE INDEX ON document_chunks
   USING ivfflat (embedding vector_cosine_ops);
   ```

2. **Connection Pooling**
   - SQLAlchemy manages connection pool
   - Default: 5 connections
   - Max overflow: 10

3. **Query Optimization**
   - Use pagination for large lists
   - Eager loading for relationships
   - Select only needed columns

### Vector Search Optimization

1. **IVFFlat Index**
   - Approximate nearest neighbor search
   - Trade-off: Speed vs accuracy
   - Good for 1000+ vectors

2. **Embedding Cache**
   - Cache query embeddings
   - Reduce API calls to Claude
   - Use Redis in production

3. **Chunk Size**
   - Target: 500 tokens per chunk
   - Overlap: 50 tokens
   - Balance: Context vs granularity

---

## Monitoring & Logging

### Application Logs

```python
# Use Python logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Key Metrics to Track

1. **API Performance**
   - Request latency (p50, p95, p99)
   - Error rate
   - Requests per second

2. **Database**
   - Query execution time
   - Connection pool usage
   - Index hit rate

3. **AI/ML**
   - Claude API latency
   - Token usage
   - Embedding generation time
   - RAG retrieval accuracy

4. **Storage**
   - Disk usage
   - Upload success rate
   - Processing time per document

---

## Scalability Considerations

### Horizontal Scaling

- **Frontend**: Multiple Next.js instances behind load balancer
- **Backend**: Multiple FastAPI workers with Gunicorn
- **Database**: PostgreSQL read replicas
- **Storage**: Distributed file system or S3

### Vertical Scaling

- **CPU**: Document processing, embedding generation
- **Memory**: Vector similarity search, large document processing
- **Disk**: Document storage, database

### Bottlenecks to Watch

1. **Claude API Rate Limits**
   - Solution: Implement request queue
   - Solution: Cache embeddings

2. **Database Connections**
   - Solution: Increase pool size
   - Solution: Use read replicas

3. **File Upload Size**
   - Solution: Chunked uploads
   - Solution: Background processing

---

## Future Architecture Enhancements

### Phase 5+

1. **Microservices**
   - Separate document processing service
   - Dedicated embedding service
   - Background job queue (Celery/RQ)

2. **Caching Layer**
   - Redis for session management
   - Cache frequent queries
   - Cache embeddings

3. **CDN**
   - Static asset delivery
   - Document download caching
   - Geographic distribution

4. **Real-time Features**
   - WebSocket connections
   - Live chat updates
   - Collaborative editing

---

## Technology Decisions & Rationale

### Why These Choices?

1. **Next.js 15**
   - Modern React framework
   - App Router for better performance
   - Built-in TypeScript support
   - Great developer experience

2. **FastAPI**
   - Fast and modern Python framework
   - Automatic API documentation
   - Native async support
   - Type hints with Pydantic

3. **PostgreSQL + pgvector**
   - Mature, reliable database
   - Native vector support
   - Single database for all data
   - ACID compliance

4. **Claude Agent SDK**
   - Specialized for agentic workflows
   - Built-in RAG support
   - Streaming responses
   - Tool use capabilities

5. **JWT Authentication**
   - Stateless authentication
   - Scalable across services
   - Standard protocol
   - Easy to implement

---

## For AI Coding Agents

When working on this codebase:

1. **Follow existing patterns**
   - API endpoints follow RESTful conventions
   - Services handle business logic
   - Schemas validate data
   - Models define database structure

2. **Code organization**
   - Keep related code together
   - One file per model/schema/service
   - Clear separation of concerns

3. **Testing strategy**
   - Unit tests for services
   - Integration tests for APIs
   - E2E tests for critical flows

4. **Documentation**
   - Update this file for architecture changes
   - Update PROGRESS.md for completed work
   - Update NEXT_STEPS.md for plans
   - Comment complex logic

This architecture is designed to be clear, maintainable, and scalable for future growth.
