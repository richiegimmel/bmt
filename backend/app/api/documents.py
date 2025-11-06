from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import time
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUpdate,
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentStats
)
from app.services.document_service import DocumentService
from app.services.text_extraction import TextExtractionService
from app.services.embedding_service import EmbeddingService


router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder: str = Query(default="/", description="Folder path for organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a new document

    - Accepts PDF, DOCX, XLSX files
    - Maximum file size: 50MB
    - Automatically saves to storage directory
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Create document
        document = DocumentService.create_document(
            db=db,
            original_filename=file.filename,
            file_size=file_size,
            file_content=file_content,
            owner_id=current_user.id,
            folder=folder
        )

        # Prepare response
        doc_response = DocumentResponse.model_validate(document)
        doc_response.is_processed = document.extracted_text is not None

        # Count chunks if any
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).count()
        doc_response.chunk_count = chunk_count if chunk_count > 0 else None

        return doc_response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    folder: Optional[str] = Query(None, description="Filter by folder"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    search: Optional[str] = Query(None, description="Search in filename and summary"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List documents with pagination and filters

    - Non-admin users see only their documents
    - Admin users see all documents
    - Supports search, folder, and file type filters
    """
    # Calculate pagination
    skip = (page - 1) * page_size

    # Admin sees all, regular users see only their own
    owner_id = None if current_user.is_admin else current_user.id

    # Get documents
    documents, total = DocumentService.list_documents(
        db=db,
        owner_id=owner_id,
        folder=folder,
        file_type=file_type,
        search=search,
        skip=skip,
        limit=page_size
    )

    # Build response with chunk counts
    doc_responses = []
    for doc in documents:
        doc_response = DocumentResponse.model_validate(doc)
        doc_response.is_processed = doc.extracted_text is not None

        # Count chunks
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        doc_response.chunk_count = chunk_count if chunk_count > 0 else None

        doc_responses.append(doc_response)

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return DocumentListResponse(
        documents=doc_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/stats", response_model=DocumentStats)
async def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document statistics

    - Non-admin users see stats for their documents only
    - Admin users see stats for all documents
    """
    owner_id = None if current_user.is_admin else current_user.id
    stats = DocumentService.get_document_stats(db=db, owner_id=owner_id)
    return stats


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get document details by ID

    - Users can only access their own documents
    - Admins can access any document
    """
    document = DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership (admin can access any)
    if not current_user.is_admin and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )

    doc_response = DocumentResponse.model_validate(document)
    doc_response.is_processed = document.extracted_text is not None

    # Count chunks
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).count()
    doc_response.chunk_count = chunk_count if chunk_count > 0 else None

    return doc_response


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download document file

    - Users can only download their own documents
    - Admins can download any document
    """
    document = DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership
    if not current_user.is_admin and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this document"
        )

    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )

    # Return file
    return FileResponse(
        path=document.file_path,
        media_type=document.mime_type,
        filename=document.original_filename
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update document metadata

    - Users can only update their own documents
    - Admins can update any document
    """
    document = DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership
    if not current_user.is_admin and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )

    # Update document
    updated_document = DocumentService.update_document(db, document_id, update_data)

    doc_response = DocumentResponse.model_validate(updated_document)
    doc_response.is_processed = updated_document.extracted_text is not None

    # Count chunks
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == updated_document.id
    ).count()
    doc_response.chunk_count = chunk_count if chunk_count > 0 else None

    return doc_response


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete document

    - Users can only delete their own documents
    - Admins can delete any document
    - Deletes both file and database record
    - Cascades to delete all document chunks
    """
    document = DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership
    if not current_user.is_admin and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )

    # Delete document
    success = DocumentService.delete_document(db, document_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

    return None


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: int,
    process_request: DocumentProcessRequest = DocumentProcessRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process document: extract text, chunk, and generate embeddings

    - Users can only process their own documents
    - Admins can process any document
    - Extracts text from PDF, DOCX, or XLSX
    - Splits text into chunks
    - Generates vector embeddings (if requested)
    - Stores chunks in database
    """
    start_time = time.time()

    document = DocumentService.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check ownership
    if not current_user.is_admin and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this document"
        )

    try:
        # Step 1: Extract text
        extracted_text, error = TextExtractionService.extract_text(document.file_path)

        if error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Text extraction failed: {error}"
            )

        if not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from document"
            )

        # Update document with extracted text
        document.extracted_text = extracted_text
        document.updated_at = datetime.utcnow()

        # Step 2: Chunk text
        chunks = TextExtractionService.chunk_text(
            extracted_text,
            chunk_size=process_request.chunk_size,
            chunk_overlap=process_request.chunk_overlap
        )

        # Step 3: Delete existing chunks for this document
        embedding_service = EmbeddingService()
        embedding_service.delete_chunks_for_document(db, document_id)

        # Step 4: Generate embeddings if requested
        embeddings = []
        if process_request.generate_embeddings:
            embeddings = embedding_service.generate_embeddings_batch(chunks)
        else:
            embeddings = [None] * len(chunks)

        # Step 5: Store chunks with embeddings
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_service.store_chunk_with_embedding(
                db=db,
                document_id=document_id,
                content=chunk_text,
                chunk_index=idx,
                embedding=embedding
            )

        # Commit document updates
        db.commit()

        # Calculate processing time
        processing_time = time.time() - start_time

        # Count successfully generated embeddings
        embeddings_generated = sum(1 for e in embeddings if e is not None)

        return DocumentProcessResponse(
            document_id=document_id,
            status="completed",
            extracted_text_length=len(extracted_text),
            chunk_count=len(chunks),
            embeddings_generated=embeddings_generated > 0,
            processing_time_seconds=round(processing_time, 2),
            message=f"Successfully processed document into {len(chunks)} chunks"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )
