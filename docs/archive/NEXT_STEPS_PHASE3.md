# Next Steps - Board Management Tool

This document outlines the immediate next steps for continuing development of the Board Management Tool.

## Current Status

✅ **Phase 1: Foundation** - Complete
✅ **Phase 2: Authentication** - Complete
⏭️ **Phase 3: Document Management** - Ready to Start
📅 **Phase 4: AI Chat Interface** - Planned

---

## Phase 3: Document Management System

### Overview
Build a complete document management system with file upload, storage, text extraction, and vector embeddings for semantic search.

### Step-by-Step Implementation Guide

#### Step 1: Backend - Document Upload Service (2-3 hours)

**File**: `backend/app/services/document_service.py`

1. Create document upload handler
   - Accept multipart/form-data
   - Validate file types (.pdf, .docx, .xlsx)
   - Validate file size (max 50MB)
   - Generate unique filenames
   - Save to storage directory

2. Create file storage utilities
   - Function to save file to disk
   - Function to generate safe filenames
   - Function to organize by folders

**File**: `backend/app/schemas/document.py`

3. Create Pydantic schemas
   - DocumentCreate
   - DocumentResponse
   - DocumentListResponse
   - DocumentUpdate

#### Step 2: Backend - Document API Endpoints (2-3 hours)

**File**: `backend/app/api/documents.py`

1. Create document endpoints:
   ```python
   POST /api/v1/documents/upload
   GET /api/v1/documents/
   GET /api/v1/documents/{id}
   GET /api/v1/documents/{id}/download
   PUT /api/v1/documents/{id}
   DELETE /api/v1/documents/{id}
   ```

2. Implement authentication requirements
   - All endpoints require authentication
   - Only owner or admin can delete
   - All users can view documents

3. Add to `main.py`:
   ```python
   from app.api import documents
   app.include_router(documents.router, prefix=f"{settings.api_prefix}/documents", tags=["Documents"])
   ```

#### Step 3: Backend - Text Extraction Service (3-4 hours)

**File**: `backend/app/services/text_extraction.py`

1. PDF text extraction
   ```python
   from PyPDF2 import PdfReader
   ```
   - Extract text page by page
   - Handle errors gracefully
   - Return text with page numbers

2. DOCX text extraction
   ```python
   from docx import Document
   ```
   - Extract all paragraphs
   - Preserve formatting metadata
   - Handle tables

3. Excel text extraction
   ```python
   from openpyxl import load_workbook
   ```
   - Extract from all sheets
   - Convert to readable format
   - Handle formulas

4. Text chunking utility
   - Split text into ~500 token chunks
   - Preserve semantic boundaries
   - Add overlap between chunks

#### Step 4: Backend - Vector Embedding Service (3-4 hours)

**File**: `backend/app/services/embedding_service.py`

1. Create embedding generator
   ```python
   from anthropic import Anthropic
   ```
   - Use Claude API for embeddings
   - Handle rate limiting
   - Batch processing support

2. Store embeddings in database
   - Create DocumentChunk records
   - Store vector embeddings
   - Link to parent document

3. Create vector search function
   - Query similar documents
   - Use pgvector similarity search
   - Return with relevance scores

**New Endpoint**:
```python
POST /api/v1/documents/{id}/process
```
- Trigger text extraction
- Generate embeddings
- Update document status

#### Step 5: Frontend - Document Upload UI (3-4 hours)

**File**: `frontend/lib/api/documents.ts`

1. Create document API service
   ```typescript
   uploadDocument(file: File): Promise<Document>
   listDocuments(): Promise<DocumentListResponse>
   getDocument(id: number): Promise<Document>
   deleteDocument(id: number): Promise<void>
   ```

**File**: `frontend/app/documents/page.tsx`

2. Create document upload page
   - Drag & drop zone
   - File list with progress
   - Upload button
   - Error handling

3. Install react-dropzone
   ```bash
   npm install react-dropzone
   ```

4. Create upload component
   - File selection
   - Upload progress
   - Success/error states

#### Step 6: Frontend - Document Browser (2-3 hours)

**File**: `frontend/app/documents/page.tsx`

1. Create document list view
   - Table or grid layout
   - Document metadata display
   - Search and filter
   - Pagination

2. Create document actions
   - Download button
   - Delete button (with confirmation)
   - View details
   - Process button

3. Add ShadCN components needed:
   ```bash
   npx shadcn@latest add table
   npx shadcn@latest add badge
   npx shadcn@latest add alert-dialog
   ```

#### Step 7: Frontend - Document Search (2 hours)

**File**: `frontend/app/documents/page.tsx`

1. Add search bar
   - Real-time search
   - Debounced API calls
   - Clear button

2. Add filters
   - File type filter
   - Date range filter
   - Folder filter

3. Add semantic search (future)
   - Vector similarity search
   - Natural language queries

#### Step 8: Testing & Polish (2-3 hours)

1. Test document upload
   - Different file types
   - Large files
   - Invalid files
   - Error scenarios

2. Test text extraction
   - Various PDF formats
   - Complex DOCX files
   - Excel with formulas

3. Test vector search
   - Semantic similarity
   - Relevance scores
   - Performance

---

## Phase 4: AI Chat Interface (After Phase 3)

### Overview
Integrate Claude Agent SDK to create an AI-powered legal assistant with document retrieval and generation capabilities.

### High-Level Steps

1. **Claude Agent SDK Setup**
   - Configure agent with system prompts
   - Define custom tools for RAG
   - Set up web search for KY statutes

2. **Chat Backend**
   - Create chat endpoint with streaming
   - Implement RAG tool
   - Track citations
   - Save chat history

3. **Chat Frontend**
   - Build chat interface
   - Stream AI responses
   - Display citations
   - Document generation UI

4. **Document Generation**
   - Template system
   - Legal document formatting
   - Download generated docs
   - Save to document library

---

## Immediate Action Items

### Before Starting Phase 3

1. ✅ Ensure Phase 2 is tested and working
2. ✅ Review PROGRESS.md for current state
3. ✅ Verify database is set up correctly
4. ✅ Test authentication flow

### To Start Phase 3 Today

1. **Backend First Approach** (Recommended)
   ```bash
   cd backend
   source venv/bin/activate

   # Create files
   touch app/services/document_service.py
   touch app/services/text_extraction.py
   touch app/schemas/document.py
   touch app/api/documents.py
   ```

2. **Start with upload endpoint**
   - Focus on Step 1-2 above
   - Test with Postman or curl
   - Then move to frontend

3. **Test incrementally**
   - Upload endpoint → Test
   - List endpoint → Test
   - Download endpoint → Test
   - Build frontend after backend works

---

## Estimated Timeline

### Phase 3 Complete Breakdown

| Task | Estimated Time | Priority |
|------|---------------|----------|
| Upload service + API | 3-4 hours | High |
| Text extraction | 3-4 hours | High |
| Vector embeddings | 3-4 hours | High |
| Frontend upload UI | 3-4 hours | High |
| Document browser | 2-3 hours | Medium |
| Search & filters | 2 hours | Medium |
| Testing & polish | 2-3 hours | High |
| **Total** | **18-25 hours** | **~3-4 sessions** |

### Phase 4 Complete Breakdown

| Task | Estimated Time | Priority |
|------|---------------|----------|
| Agent SDK setup | 2-3 hours | High |
| RAG implementation | 4-5 hours | High |
| Chat backend + streaming | 4-5 hours | High |
| Chat frontend UI | 3-4 hours | High |
| Citation system | 2-3 hours | Medium |
| Document generation | 4-5 hours | High |
| Testing & polish | 3-4 hours | High |
| **Total** | **22-29 hours** | **~4-5 sessions** |

---

## Development Tips

### For Document Processing

1. **Handle file types gracefully**
   - Not all PDFs extract cleanly
   - Use try/except for each extraction
   - Log extraction failures
   - Store partial results

2. **Chunking strategy**
   - Use tiktoken to count tokens
   - Target ~500 tokens per chunk
   - Overlap chunks by 50 tokens
   - Preserve paragraph boundaries

3. **Vector embeddings**
   - Batch embed multiple chunks
   - Cache embeddings
   - Handle API rate limits
   - Store embedding model version

### For Chat Interface

1. **Streaming is critical**
   - Users expect real-time responses
   - Use SSE or WebSockets
   - Show typing indicators
   - Handle disconnections

2. **RAG quality**
   - Retrieve top 5-10 most relevant chunks
   - Include document metadata
   - Rank by relevance
   - Filter by date/type if needed

3. **Citations**
   - Link to exact document + page
   - Show preview on hover
   - Allow click to open document
   - Track citation clicks

---

## API Design Reference

### Document Endpoints (Phase 3)

```
POST   /api/v1/documents/upload
GET    /api/v1/documents/
GET    /api/v1/documents/{id}
GET    /api/v1/documents/{id}/download
PUT    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
POST   /api/v1/documents/{id}/process
GET    /api/v1/documents/search?q={query}
```

### Chat Endpoints (Phase 4)

```
POST   /api/v1/chat/sessions
GET    /api/v1/chat/sessions
GET    /api/v1/chat/sessions/{id}
DELETE /api/v1/chat/sessions/{id}
POST   /api/v1/chat/sessions/{id}/messages
GET    /api/v1/chat/sessions/{id}/messages
POST   /api/v1/chat/stream (SSE)
```

---

## Resources

### Documentation to Reference

- **FastAPI File Uploads**: https://fastapi.tiangolo.com/tutorial/request-files/
- **Claude Agent SDK**: `/home/richie/bmt/CLAUDE_AGENT_SDK.md`
- **pgvector**: https://github.com/pgvector/pgvector
- **PyPDF2**: https://pypdf2.readthedocs.io/
- **python-docx**: https://python-docx.readthedocs.io/
- **react-dropzone**: https://react-dropzone.js.org/

### Helpful Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Database migrations
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head

# Install new Python packages
pip install package-name
pip freeze > requirements.txt

# Install new npm packages
npm install package-name
```

---

## Questions to Answer Before Starting

1. **Document organization**
   - Do we need folder/category support immediately?
   - Or start with flat list?
   - **Recommendation**: Start flat, add folders in polish

2. **Processing strategy**
   - Process on upload automatically?
   - Or manual "Process" button?
   - **Recommendation**: Automatic processing with progress indicator

3. **Search priority**
   - Full-text search or vector search first?
   - **Recommendation**: Vector search (semantic) as it's the core feature

4. **File storage**
   - Store in database or filesystem?
   - **Recommendation**: Filesystem (already designed for ZFS)

---

## Success Criteria

### Phase 3 Complete When:

- [ ] Can upload PDF, DOCX, XLSX files
- [ ] Files stored on disk with metadata in DB
- [ ] Text extracted from all file types
- [ ] Vector embeddings generated and stored
- [ ] Can list all documents
- [ ] Can download documents
- [ ] Can delete documents
- [ ] Can search documents semantically
- [ ] UI is responsive and user-friendly
- [ ] Error handling works correctly

### Phase 4 Complete When:

- [ ] Can create chat sessions
- [ ] Can send messages and get AI responses
- [ ] Responses stream in real-time
- [ ] AI retrieves relevant documents (RAG)
- [ ] Citations show up with links
- [ ] Can generate legal documents
- [ ] Generated docs downloadable
- [ ] Chat history persists
- [ ] Web search works for KY statutes
- [ ] System is production-ready

---

## Notes for AI Coding Agents

When picking up this project:

1. **Always start by reading**:
   - PROGRESS.md - Current state
   - This file (NEXT_STEPS.md) - What to do next
   - ARCHITECTURE.md - System design
   - PROJECT_CHARTER.md - Original requirements

2. **Test authentication first**:
   ```bash
   # Start backend
   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0

   # Visit http://10.0.2.134:8000/docs
   # Login with admin/Admin123!
   ```

3. **Work incrementally**:
   - Build one feature at a time
   - Test before moving on
   - Commit working code
   - Update PROGRESS.md

4. **Ask before major decisions**:
   - Architecture changes
   - New dependencies
   - Schema modifications

5. **Keep documentation updated**:
   - Update PROGRESS.md after completing features
   - Add notes to this file if needed
   - Document any issues encountered

---

## Contact & Support

For questions or issues:
- Review existing documentation first
- Check PROGRESS.md for known issues
- Consult PROJECT_CHARTER.md for requirements
- Check API docs at http://10.0.2.134:8000/docs

**Ready to build Phase 3!** 🚀
