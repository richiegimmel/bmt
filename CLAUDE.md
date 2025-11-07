# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Board Management Tool (BMT) - A full-stack web application for board members of Atlas Machine and Supply, Inc. to manage board affairs, organize documents, and interact with an AI legal advisor.

**Tech Stack:**
- Frontend: Next.js 16 (React 19) with TypeScript, Tailwind CSS v4, shadcn/ui components
- Backend: FastAPI (Python 3.12) with SQLAlchemy
- Database: PostgreSQL with pgvector extension
- AI: Claude (Anthropic) for chat/legal advice, Voyage AI (voyage-law-2) for embeddings
- Storage: Local filesystem (ZFS)

## Development Setup

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with database credentials, API keys

# Run database migrations
alembic upgrade head

# Create initial admin user
python create_admin.py <email> <username> <password> <full_name>

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local if needed

# Start development server
npm run dev
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Testing
The project uses pytest for backend testing:
```bash
cd backend
source venv/bin/activate
pytest
pytest tests/test_specific.py  # Run specific test file
pytest -v  # Verbose output
```

## Architecture

### Backend Structure

**Core Application Flow:**
1. `app/main.py` - FastAPI application entry point, CORS configuration, router registration
2. `app/core/` - Core functionality shared across the app
   - `config.py` - Pydantic settings loaded from environment variables
   - `database.py` - SQLAlchemy engine, session management, `get_db()` dependency
   - `security.py` - JWT auth, password hashing, `get_current_user()` dependency

**Data Layer:**
- `app/models/` - SQLAlchemy ORM models
  - `user.py` - User model with admin role support
  - `document.py` - Document and DocumentChunk models (with pgvector embeddings)
  - `chat.py` - ChatSession and ChatMessage models
- `alembic/` - Database migrations

**API Layer:**
- `app/api/` - FastAPI routers (all mounted at `/api/v1`)
  - `auth.py` - Login, register, token refresh
  - `users.py` - User management (admin only)
  - `documents.py` - Document upload, processing, retrieval
  - `chat.py` - Chat sessions, streaming responses
  - `document_generation.py` - Generate legal documents from templates

**Service Layer:**
- `app/services/` - Business logic separated from API endpoints
  - `chat_service_sdk.py` - Production chat service using Claude Agent SDK with custom RAG and web search tools
  - `chat_service.py` - Legacy chat service with direct Claude API integration (not currently used)
  - `document_service.py` - Document processing, text extraction, chunking
  - `embedding_service.py` - Voyage AI integration for vector embeddings
  - `text_extraction.py` - Extract text from PDF, DOCX, XLSX (includes OCR support via pytesseract)
  - `web_search.py` - Web search for Kentucky legal statutes
  - `document_generation.py` - Generate DOCX/PDF from templates (board resolutions, minutes, etc.)

**Document Processing Pipeline:**
1. Upload → `documents.py` router
2. Text extraction → `text_extraction.py` (PDF/DOCX/XLSX support, OCR for scanned PDFs)
3. Chunking → `document_service.py` (chunks stored in `DocumentChunk` table)
4. Embedding generation → `embedding_service.py` (Voyage AI voyage-law-2 model)
5. Storage → PostgreSQL with pgvector for semantic search

**Chat/RAG Pipeline:**
1. User message → `chat.py` router
2. Query embedding → `embedding_service.py`
3. Semantic search → pgvector similarity search on DocumentChunk table
4. Context assembly → Retrieved chunks + optional web search results
5. Claude API → Streaming response with citations
6. Response → Server-Sent Events (SSE) to frontend

### Frontend Structure

**App Router (Next.js 16):**
- `app/` - Next.js app directory
  - `layout.tsx` - Root layout with AuthProvider context
  - `page.tsx` - Landing page (redirects to dashboard if authenticated)
  - `login/`, `register/` - Authentication pages
  - `dashboard/` - Main dashboard with document stats
  - `documents/` - Document management UI (upload, browse, delete)
  - `chat/` - AI chat interface with streaming responses
  - `generate/` - Document generation UI

**Shared Components:**
- `components/ui/` - shadcn/ui components (button, dialog, dropdown-menu, etc.)
- `components/protected-route.tsx` - Client-side route protection wrapper

**State Management:**
- `contexts/` - React Context providers
  - Auth context for user session management

**API Integration:**
- `lib/api/` - API client functions
  - `client.ts` - Base API client with token handling
  - `auth.ts` - Authentication API calls
  - `documents.ts` - Document API calls
  - `chat.ts` - Chat API calls (includes SSE streaming)
  - `document-generation.ts` - Document generation API calls

**Styling:**
- Tailwind CSS v4 with shadcn/ui components
- Lucide icons

### Authentication Flow

1. User logs in → `POST /api/v1/auth/login`
2. Backend validates credentials → Returns access token (JWT, 30min) + refresh token (7 days)
3. Frontend stores tokens in localStorage
4. Protected routes use `ProtectedRoute` component → Checks token validity
5. API calls include `Authorization: Bearer <token>` header via `client.ts`
6. Token refresh → `POST /api/v1/auth/refresh` with refresh token
7. Backend uses `get_current_user()` dependency to validate tokens and load user

### Key Features

**Document Management:**
- Upload PDF, DOCX, XLSX files
- OCR support for scanned PDFs (pytesseract)
- Automatic text extraction and chunking
- Vector embeddings for semantic search (Voyage AI)
- Folder organization

**AI Legal Advisor:**
- Claude-powered chat interface
- RAG (Retrieval-Augmented Generation) using uploaded documents
- Web search integration for Kentucky statutes (lrc.ky.gov, legislature.ky.gov)
- Streaming responses via SSE
- Citation of sources (documents and web results)

**Document Generation:**
- Templates: Board resolutions, meeting minutes, notices, consent actions
- Output formats: DOCX, PDF
- Pre-populated with company information (Atlas Machine and Supply, Inc.)

**User Management:**
- JWT-based authentication
- Two roles: regular users and admins
- Admin users can manage other users
- All users have access to all features except user management

## Important Notes

**Database:**
- Requires PostgreSQL with pgvector extension installed
- Connection string format: `postgresql://user:pass@host:port/dbname`
- Migrations managed with Alembic

**API Keys Required:**
- `ANTHROPIC_API_KEY` - For Claude API (chat, legal advice)
- `VOYAGE_API_KEY` - For Voyage AI embeddings (voyage-law-2 model)

**CORS Configuration:**
- Backend explicitly allows `http://localhost:3000` and `http://10.0.2.134:3000`
- Update `app/main.py` CORS middleware if frontend runs on different origin

**File Storage:**
- Uploaded files stored in `backend/uploads/`
- Processed documents stored in `backend/storage/`
- Both directories created automatically

**Embedding Dimensions:**
- Voyage AI voyage-law-2 uses 1024-dimensional embeddings
- DocumentChunk.embedding column is `Vector(1024)`

**Chat System:**
- System prompt configured in `chat_service_sdk.py` - designed for Kentucky law and board governance
- Uses Claude Agent SDK (`chat_service_sdk.py`) for production with custom RAG and web search tools
- Legacy implementation available in `chat_service.py` (not currently used)
- Streaming via SSE using `sse-starlette` package

## Common Commands

**Backend:**
```bash
# Start dev server
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Run migrations
cd backend && source venv/bin/activate && alembic upgrade head

# Create migration
cd backend && source venv/bin/activate && alembic revision --autogenerate -m "description"

# Create admin user
cd backend && source venv/bin/activate && python create_admin.py

# Run tests
cd backend && source venv/bin/activate && pytest
```

**Frontend:**
```bash
# Start dev server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Run linter
cd frontend && npm run lint
```

## Project Context

This is a corporate governance tool for a single company (Atlas Machine and Supply, Inc.), a C Corporation in Kentucky owned by the Richard F. Gimmel III 2023 Decanted Gift Trust. The AI legal advisor is specifically tuned for Kentucky corporate law and board governance matters.

Reference PROJECT_CHARTER.md for detailed project scope and use cases.
