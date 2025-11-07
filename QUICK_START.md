# Quick Start Guide - Board Management Tool

## Starting the Application

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Access URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Login Credentials

```
Email: admin@atlas.com
Password: Admin123!
```

---

## Using New Features

### 1. Document Generation

**Access**: http://localhost:3000/generate

**Available Templates:**
1. **Board Resolution**
   - Resolution title and number
   - WHEREAS clauses (multiple)
   - RESOLVED clauses (multiple)
   - Secretary name

2. **Meeting Minutes**
   - Meeting details (date, time, location)
   - Attendees and absent members
   - Matters discussed
   - Resolutions adopted

3. **Meeting Notice**
   - Meeting date, time, and location
   - Agenda items
   - Recipient information

4. **Consent Action**
   - Resolutions to be approved
   - Director signatures

**How to Use:**
1. Select a template
2. Fill in required fields (marked with *)
3. Add array items (WHEREAS clauses, agenda items, etc.)
4. Choose format (DOCX or PDF)
5. Optionally save to document library
6. Click "Generate Document" or "Generate & Download"

**API Usage:**
```bash
# List templates
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/document-generation/templates

# Generate document
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_type": "board_resolution",
    "title": "Board Resolution - November 2025",
    "format": "pdf",
    "save_to_documents": true,
    "data": {
      "resolution_title": "Approve New Fiscal Policy",
      "resolved_clauses": [
        "The Board approves the new fiscal policy effective immediately"
      ]
    }
  }' \
  http://localhost:8000/api/v1/document-generation/generate
```

---

### 2. AI Chat with Agent SDK

**Access**: http://localhost:3000/chat

**New Capabilities:**
1. **Automatic Tool Selection** - Claude decides when to use RAG or web search
2. **RAG Document Search** - Searches uploaded documents automatically
3. **Web Search** - Searches Kentucky statutes when relevant

**Example Queries:**

**For Document Search (RAG):**
```
"What does our policy say about board meeting quorum?"
"Find information about fiscal responsibilities in our documents"
"What are the requirements for annual meetings?"
```

**For Kentucky Statute Search:**
```
"What does KRS 271B say about board duties?"
"Find Kentucky statute on corporate governance"
"What are Kentucky's requirements for board resolutions?"
```

**How It Works:**
1. Type your question
2. Claude automatically:
   - Searches uploaded documents if relevant
   - Searches web for Kentucky statutes if needed
   - Combines information from both sources
   - Provides cited answer with sources

**Tool Activation:**
- **RAG Tool**: Activated for questions about uploaded documents
- **Web Search Tool**: Activated when query contains:
  - "kentucky statute"
  - "krs" or "k.r.s"
  - "kentucky law"
  - "ky statute"
  - Similar keywords

---

### 3. Document Upload & Processing

**Access**: http://localhost:3000/documents

**Supported Formats:**
- PDF (including scanned PDFs with OCR)
- Word documents (.docx, .doc)
- Excel spreadsheets (.xlsx, .xls)

**Maximum Size:** 50MB

**Process:**
1. Drag and drop files or click to select
2. Files automatically upload and process
3. Text extracted and chunked
4. Embeddings generated with Voyage AI
5. Ready for chat/search in ~2-10 seconds

---

## Architecture Overview

### Chat Flow with Agent SDK

```
User Question
    ↓
Claude Agent SDK Client
    ↓
[Claude analyzes question]
    ↓
Tool Selection:
├── search_documents (RAG)
│   ├── Generate embedding
│   ├── Search similar chunks
│   └── Return top 5 results
├── search_kentucky_statutes (Web)
│   ├── Detect Kentucky law query
│   ├── Search DuckDuckGo
│   └── Return official sources
└── Direct response (no tools)
    ↓
Claude composes answer with citations
    ↓
Streaming response to user
```

### Document Generation Flow

```
Template Selection
    ↓
Dynamic Form Generation
    ↓
Field Validation
    ↓
Template Renderer
├── DOCX: python-docx
└── PDF: reportlab
    ↓
Optional: Save to Library
    ↓
Download or View
```

---

## Configuration

### Environment Variables

**Backend (.env):**
```bash
# Database
DATABASE_URL=postgresql://bmt_user:PASSWORD@localhost:5432/board_management_tool

# Security
SECRET_KEY=your_secret_key_here
DEBUG=true

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-...
VOYAGE_API_KEY=pa-...

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Common Tasks

### Adding New Documents
1. Go to http://localhost:3000/documents
2. Click "Upload Documents" or drag & drop
3. Wait for processing (shows progress)
4. Documents appear in list when ready

### Generating Board Resolution
1. Go to http://localhost:3000/generate
2. Select "Board Resolution"
3. Enter resolution title and clauses
4. Choose PDF or DOCX
5. Generate & download

### Asking Legal Questions
1. Go to http://localhost:3000/chat
2. Click "New Session"
3. Ask your question
4. Claude automatically searches documents and/or web
5. Review answer with citations

### Managing Chat Sessions
- **Create New**: Click "New Chat" button
- **Switch Session**: Select from session list
- **Delete Session**: Click trash icon
- **View History**: All messages preserved per session

---

## Troubleshooting

### Backend Won't Start
```bash
# Check if reportlab is installed
pip install reportlab==4.2.2

# Verify all imports
python -c "from app.main import app; print('OK')"

# Check database connection
python -c "from app.core.database import engine; engine.connect(); print('DB OK')"
```

### Frontend Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run dev
```

### Chat Not Responding
1. Check Anthropic API key in `.env`
2. Verify backend is running
3. Check browser console for errors
4. Ensure database is accessible

### Document Generation Fails
1. Verify reportlab is installed
2. Check storage directory exists: `backend/storage`
3. Ensure write permissions
4. Check API key authentication

### Web Search Not Working
1. Check internet connectivity
2. Verify httpx is installed: `pip list | grep httpx`
3. Look for keyword triggers in query
4. Check backend logs for errors

---

## API Quick Reference

### Get Auth Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@atlas.com","password":"Admin123!"}'
```

### List Templates
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/document-generation/templates
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf"
```

### Create Chat Session
```bash
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Chat"}'
```

### Send Chat Message (Streaming)
```bash
curl -N http://localhost:8000/api/v1/chat/sessions/1/messages/stream \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is KRS 271B?"}'
```

---

## Performance Tips

### For Large Document Libraries
1. Use specific search queries
2. Limit chat context to recent sessions
3. Regularly clean up old sessions
4. Monitor database size

### For Faster Chat Responses
1. Be specific in questions
2. Mention document names when known
3. Use keywords to trigger right tools
4. Keep sessions focused on one topic

### For Document Generation
1. Prepare data in advance
2. Use templates consistently
3. Save frequently used formats
4. Batch generate when possible

---

## Support

### Documentation
- **Architecture**: `/docs/ARCHITECTURE.md`
- **Setup Guide**: `/SETUP.md`
- **Testing Guide**: `/docs/TESTING_GUIDE.md`
- **Current Status**: `/CURRENT_STATUS.md`
- **Implementation Summary**: `/IMPLEMENTATION_SUMMARY.md`

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Getting Help
1. Check error messages in browser console
2. Review backend logs in terminal
3. Consult documentation files
4. Check API docs for endpoint details

---

## What's New

### Recent Additions (Nov 2025)
- ✅ **Document Generation** - 4 legal templates, DOCX/PDF export
- ✅ **Web Search** - Automatic Kentucky statute lookup
- ✅ **Agent SDK** - Intelligent tool orchestration
- ✅ **Custom MCP Tools** - RAG and web search as tools
- ✅ **Improved Documentation** - Accurate status and guides

### Key Improvements
- Automatic tool selection by Claude
- Better source attribution
- Professional document templates
- Enhanced legal research capabilities
- More accurate documentation

---

**Last Updated**: November 6, 2025
