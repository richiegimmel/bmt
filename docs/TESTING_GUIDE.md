# Testing Guide - AI Chat with RAG

This guide provides simple tests to verify that the AI chat system, embeddings, and document retrieval are working correctly.

## Prerequisites

- Backend running on http://10.0.2.134:8000
- Frontend running on http://10.0.2.134:3000
- Logged in as admin user

---

## Test 1: Basic Chat Functionality (No Documents)

**Purpose**: Verify Claude AI is responding without document context

### Steps:
1. Navigate to http://10.0.2.134:3000/chat
2. Click "New Chat" button
3. Type a simple question: **"What is Kentucky?"**
4. Press Enter or click Send

### Expected Results:
- ✅ Message appears in chat immediately (user message)
- ✅ AI response starts streaming within 2-3 seconds
- ✅ Response appears word-by-word (streaming)
- ✅ No citations appear (since no documents uploaded)
- ✅ AI provides a general answer about Kentucky

### Success Criteria:
- Streaming works smoothly
- No errors in browser console
- Response is coherent and relevant

---

## Test 2: Document Upload & Processing

**Purpose**: Verify document upload and embedding generation with Voyage AI

### Steps:
1. Navigate to http://10.0.2.134:3000/documents
2. Create a simple test document on your computer:

   **Create file: `test_legal_doc.txt`**
   ```
   BOARD POLICY - MEETING PROCEDURES

   Section 1: Regular Meetings
   The Board shall meet on the first Tuesday of each month at 7:00 PM.
   All meetings must be posted 48 hours in advance.

   Section 2: Quorum Requirements
   A quorum consists of a majority of board members.
   At least 5 of 7 members must be present to conduct business.

   Section 3: Voting Procedures
   All votes require a simple majority to pass.
   The board chair votes only to break ties.

   Section 4: Public Comment
   Public comment is allowed for 3 minutes per speaker.
   Total public comment period shall not exceed 30 minutes.
   ```

3. Save as a `.txt` file or create a `.docx` file with this content
4. Upload the document via drag-and-drop or file selector
5. Wait for processing to complete

### Expected Results:
- ✅ File uploads successfully
- ✅ Processing status shows "Processing..." or similar
- ✅ After processing, status changes to "Processed" or shows completion
- ✅ No errors in console

### Verify Embeddings in Database:
Run this command to check:
```bash
PGPASSWORD=xSjYiGI97w45vW55k5or7Dfr psql -U bmt_user -d board_management_tool -h localhost -c "
SELECT
    d.id,
    d.filename,
    COUNT(dc.id) as chunk_count,
    COUNT(CASE WHEN dc.embedding IS NOT NULL THEN 1 END) as embeddings_count
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.filename
ORDER BY d.id DESC
LIMIT 5;
"
```

### Expected Output:
```
 id |      filename       | chunk_count | embeddings_count
----+--------------------+-------------+------------------
  1 | test_legal_doc.txt |           4 |                4
```

### Success Criteria:
- Document appears in list
- `chunk_count` > 0 (document was chunked)
- `embeddings_count` = `chunk_count` (all chunks have embeddings)

---

## Test 3: RAG - Document Retrieval & Citations

**Purpose**: Verify semantic search and citation system

### Steps:
1. Go back to Chat page: http://10.0.2.134:3000/chat
2. Create a new chat session (click "New Chat")
3. Ask a question about the uploaded document:

   **Test Question 1**: "What time do board meetings start?"

4. Wait for response
5. Ask a follow-up question:

   **Test Question 2**: "How many board members are needed for a quorum?"

### Expected Results:

**For Question 1:**
- ✅ AI responds with: "7:00 PM" or "7 PM" or similar
- ✅ Citations appear showing `test_legal_doc.txt`
- ✅ Citation shows relevant section (Section 1)
- ✅ Response references the document content

**For Question 2:**
- ✅ AI responds with: "5 of 7 members" or "majority" or similar
- ✅ Citations appear with document reference
- ✅ Response is accurate based on uploaded content

### Verify in Browser DevTools:
Open browser console (F12) → Network tab:
- Look for request to `/api/v1/chat/sessions/{id}/messages/stream`
- Check the response includes citation data

### Success Criteria:
- AI provides accurate answers from document
- Citations link to correct document
- Multiple relevant chunks retrieved (up to 5)
- Answers are specific to YOUR document, not general knowledge

---

## Test 4: Voyage AI Embeddings Quality

**Purpose**: Test semantic similarity (not just keyword matching)

### Steps:
1. In the same chat, ask semantically similar questions using different words:

   **Test Question 3**: "When does the board convene each month?"

   (This asks about meeting time using different words)

### Expected Results:
- ✅ AI understands this is asking about meeting schedule
- ✅ Retrieves same document chunks as Question 1
- ✅ Provides correct answer (first Tuesday, 7 PM)
- ✅ Citations appear

### Success Criteria:
- Semantic search works (not just keyword matching)
- voyage-law-2 model finds relevant content even with different phrasing

---

## Test 5: Streaming Performance

**Purpose**: Verify real-time streaming works correctly

### Steps:
1. Ask a question that requires a longer response:

   **Test Question 4**: "Summarize all the board meeting procedures from the document"

### Expected Results:
- ✅ Response starts appearing within 1-2 seconds
- ✅ Text streams smoothly (word by word or phrase by phrase)
- ✅ No buffering or delays
- ✅ Citations appear before or during streaming
- ✅ "Thinking..." indicator shows while streaming
- ✅ Indicator disappears when complete

### Success Criteria:
- Smooth streaming experience
- No frozen UI
- Complete response received

---

## Test 6: Multiple Documents RAG

**Purpose**: Test retrieval across multiple documents

### Steps:
1. Upload a second document with different content:

   **Create file: `kentucky_statutes.txt`**
   ```
   KENTUCKY REVISED STATUTES - OPEN MEETINGS

   KRS 61.810: Public meetings must be open to the public
   All meetings of public agencies shall be open to the public.

   KRS 61.815: Notice Requirements
   Written notice must be provided at least 24 hours before special meetings.

   KRS 61.820: Executive Sessions
   Executive sessions are permitted only for specific purposes including:
   - Personnel matters
   - Pending litigation
   - Property acquisition
   ```

2. Wait for processing
3. In chat, ask: **"What does Kentucky law say about meeting notice requirements?"**

### Expected Results:
- ✅ AI retrieves from BOTH documents (if relevant)
- ✅ Citations show `kentucky_statutes.txt`
- ✅ Answer mentions "24 hours" from statutes
- ✅ May also reference "48 hours" from board policy
- ✅ AI can differentiate between general law and board policy

### Success Criteria:
- Multi-document retrieval works
- Most relevant chunks retrieved regardless of source
- Citations clearly identify source documents

---

## Test 7: Session Management

**Purpose**: Verify chat sessions work correctly

### Steps:
1. Create 3 different chat sessions
2. In each session, ask a different question
3. Switch between sessions
4. Verify conversation history persists
5. Delete one session

### Expected Results:
- ✅ Each session maintains its own conversation history
- ✅ Switching sessions shows correct messages
- ✅ Deleting a session removes it from sidebar
- ✅ Deleted session's messages are gone

---

## Test 8: Error Handling

**Purpose**: Verify graceful error handling

### Test Cases:

**8a. Invalid/Empty Message**
- Try to send an empty message
- Expected: Button disabled or error message

**8b. Very Long Message**
- Send a message with 1000+ words
- Expected: Either accepts it or shows character limit warning

**8c. Special Characters**
- Send: "What about [Section 1] & <html>?"
- Expected: AI responds normally, no XSS issues

---

## Verification Commands

### Check Backend Logs
```bash
# In backend terminal, look for:
# - "DEBUG: credentials = ..." (if still enabled)
# - Successful embedding generation
# - No error tracebacks
```

### Check Embedding Generation
```bash
PGPASSWORD=xSjYiGI97w45vW55k5or7Dfr psql -U bmt_user -d board_management_tool -h localhost -c "
SELECT
    id,
    content,
    LENGTH(embedding::text) as embedding_size
FROM document_chunks
LIMIT 3;
"
```

Expected: `embedding_size` should be a large number (embeddings are 1024-dimensional vectors)

### Check Chat Messages with Citations
```bash
PGPASSWORD=xSjYiGI97w45vW55k5or7Dfr psql -U bmt_user -d board_management_tool -h localhost -c "
SELECT
    id,
    role,
    LEFT(content, 100) as content_preview,
    citations IS NOT NULL as has_citations
FROM chat_messages
ORDER BY created_at DESC
LIMIT 5;
"
```

---

## Quick Smoke Test (1 Minute)

If you just want a quick verification:

1. **Upload a document** → Check it processes
2. **Go to chat** → Create new session
3. **Ask about document** → "What does the document say about [topic]?"
4. **Verify**:
   - ✅ Response mentions document content
   - ✅ Citations appear
   - ✅ Streaming works

---

## Troubleshooting

### No Citations Appear
- Check: Are documents processed? (status = "processed")
- Check: Do chunks have embeddings? (run verification command above)
- Check: Is VOYAGE_API_KEY set correctly?

### Wrong/Irrelevant Answers
- Check: Relevance score threshold (currently 0.65 in chat_service.py)
- Lower threshold if needed for testing
- Check: Are embeddings actually generated?

### Streaming Doesn't Work
- Check browser console for errors
- Check Network tab for SSE connection
- Verify backend is sending `text/event-stream`

### "Not authenticated" Error
- Clear browser localStorage
- Login again
- Check token is stored as `access_token`

---

## Success Checklist

After running all tests, you should have verified:

- ✅ Claude AI responds correctly
- ✅ Streaming works smoothly
- ✅ Documents upload and process
- ✅ Embeddings generated with Voyage AI (voyage-law-2)
- ✅ Semantic search retrieves relevant chunks
- ✅ Citations appear and link to source documents
- ✅ Multi-document retrieval works
- ✅ Session management functional
- ✅ Error handling graceful

---

## Next Steps

If all tests pass:
- Upload real legal documents
- Test with actual use cases
- Fine-tune relevance threshold if needed
- Add more documents to knowledge base

If tests fail:
- Check backend logs for errors
- Verify API keys (ANTHROPIC_API_KEY, VOYAGE_API_KEY)
- Check database connectivity
- Review CORS settings
- Ensure all services restarted after changes

---

## API Test (Optional - For Developers)

Test the API directly with curl:

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://10.0.2.134:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create chat session
SESSION=$(curl -s -X POST http://10.0.2.134:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"API Test"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Session ID: $SESSION"

# Stream a message
curl -N http://10.0.2.134:8000/api/v1/chat/sessions/$SESSION/messages/stream \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello, are you working?"}'
```

You should see Server-Sent Events streaming back with the AI response!

---

**Happy Testing! 🚀**
