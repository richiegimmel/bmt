from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class DocumentCreate(BaseModel):
    """Schema for creating a document"""
    filename: str = Field(..., description="Original filename")
    folder: Optional[str] = Field(default="/", description="Folder path")


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    filename: Optional[str] = Field(None, description="Updated filename")
    folder: Optional[str] = Field(None, description="Updated folder path")
    summary: Optional[str] = Field(None, description="Document summary")


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_type: str
    file_size: int
    mime_type: str
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    folder: str
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed fields
    is_processed: bool = Field(default=False, description="Whether text has been extracted")
    chunk_count: Optional[int] = Field(default=None, description="Number of chunks created")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentProcessRequest(BaseModel):
    """Schema for document processing request"""
    generate_embeddings: bool = Field(default=True, description="Generate vector embeddings")
    chunk_size: int = Field(default=500, ge=100, le=2000, description="Target tokens per chunk")
    chunk_overlap: int = Field(default=50, ge=0, le=500, description="Overlap between chunks")


class DocumentProcessResponse(BaseModel):
    """Schema for document processing response"""
    document_id: int
    status: str
    extracted_text_length: int
    chunk_count: int
    embeddings_generated: bool
    processing_time_seconds: float
    message: str


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk"""
    id: int
    document_id: int
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    created_at: datetime

    # For search results
    relevance_score: Optional[float] = Field(default=None, description="Similarity score for search results")

    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """Schema for semantic document search"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    min_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    file_type: Optional[str] = Field(default=None, description="Filter by file type")
    folder: Optional[str] = Field(default=None, description="Filter by folder")


class DocumentSearchResponse(BaseModel):
    """Schema for document search results"""
    chunks: List[DocumentChunkResponse]
    total_found: int
    query: str
    search_time_seconds: float


class DocumentStats(BaseModel):
    """Schema for document statistics"""
    total_documents: int
    total_size_bytes: int
    by_file_type: dict
    by_folder: dict
    processed_count: int
    unprocessed_count: int
