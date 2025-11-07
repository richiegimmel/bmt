# Board Management Tool

A full-stack web application for managing board affairs at Atlas Machine and Supply, Inc.

## Overview

The Board Management Tool provides document organization, AI-powered legal assistance, and document generation capabilities for corporate board management.

## Features

### ✅ Implemented (Phase 1-4)
- **User Authentication** - JWT-based auth with refresh tokens
- **Document Management** - Upload, organize, search, and download documents
- **File Processing** - Extract text from PDF, DOCX, XLSX files
- **OCR Support** - Automatic OCR for scanned/image-based PDFs
- **Text Chunking** - Intelligent document chunking for embeddings
- **Role-Based Access** - Admin and user roles with permissions
- **Document Statistics** - Track uploads, processing status, and file types
- **AI Chat Interface** - Streaming chat with Claude Sonnet 4.5
- **Document Retrieval (RAG)** - Semantic search with citations using Voyage AI
- **Vector Search** - Legal-specialized embeddings (voyage-law-2, 1024 dimensions)
- **Citation Tracking** - Source attribution with relevance scores

### ❌ Not Yet Implemented
- **Automated Document Generation** - Template-based creation of board resolutions, minutes, notices
- **Web Search Integration** - Real-time lookup of Kentucky statutes

## Tech Stack

### Frontend
- Next.js 15 (App Router)
- React 18
- TypeScript
- Tailwind CSS v4
- ShadCN UI Components
- Lucide Icons

### Backend
- FastAPI (Python 3.12)
- PostgreSQL 16 with pgvector 0.8.0
- Anthropic Claude (Sonnet 4.5)
- Voyage AI (voyage-law-2 embeddings)
- JWT Authentication
- Alembic (migrations)

### Storage
- Local filesystem (ZFS-backed)
- PostgreSQL for metadata
- pgvector for document embeddings

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 16+ with pgvector extension
- Tesseract OCR (for scanned PDF support)
- Poppler (for PDF processing)
- Anthropic API key for Claude
- Voyage AI API key for embeddings

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# Install backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb board_management_tool

# Enable pgvector extension
psql board_management_tool -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
cd backend
alembic upgrade head
```

### 3. Environment Configuration

```bash
# Copy example environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env files with your configuration
```

### 4. Run Development Servers

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
bmt/
├── frontend/           # Next.js application
│   ├── app/           # App router pages
│   ├── components/    # React components
│   ├── lib/          # Utilities and helpers
│   └── public/       # Static assets
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── core/     # Configuration
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── main.py   # Application entry
│   ├── alembic/      # Database migrations
│   ├── storage/      # Document storage
│   └── uploads/      # Temporary uploads
└── docs/             # Documentation
```

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## License

Proprietary - Atlas Machine and Supply, Inc.
