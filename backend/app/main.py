from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import all models to ensure SQLAlchemy knows about them
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentCategory, DocumentTag, DocumentVersion
from app.models.chat import ChatSession, ChatMessage
from app.models.meeting import Meeting, MeetingAttendee, MeetingDocument, AgendaItem
from app.models.board import BoardMember, Committee, CommitteeMember, OfficerRole
from app.models.resolution import Resolution, ResolutionVote, ActionItem
from app.models.compliance import ComplianceItem, ComplianceHistory
from app.models.notification import Notification

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# Configure CORS
# Explicitly set CORS origins to ensure they're loaded correctly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://10.0.2.134:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Board Management Tool API",
        "status": "online"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers
from app.api import auth, users, documents, chat, document_generation, document_categories, dashboard

app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.api_prefix}/users", tags=["Users"])
app.include_router(dashboard.router, prefix=f"{settings.api_prefix}", tags=["Dashboard"])
app.include_router(documents.router, prefix=f"{settings.api_prefix}/documents", tags=["Documents"])
app.include_router(document_categories.router, prefix=f"{settings.api_prefix}/documents", tags=["Document Categories"])
app.include_router(chat.router, prefix=f"{settings.api_prefix}/chat", tags=["Chat"])
app.include_router(document_generation.router, prefix=f"{settings.api_prefix}/document-generation", tags=["Document Generation"])
