from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import all models to ensure SQLAlchemy knows about them
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
from app.api import auth, users

app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.api_prefix}/users", tags=["Users"])

# Future routers
# from app.api import documents, chat
# app.include_router(documents.router, prefix=f"{settings.api_prefix}/documents", tags=["Documents"])
# app.include_router(chat.router, prefix=f"{settings.api_prefix}/chat", tags=["Chat"])
