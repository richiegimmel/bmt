import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, BinaryIO
from pathlib import Path
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.doc', '.xls'}
MIME_TYPE_MAP = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Base storage directory
STORAGE_BASE = Path("storage")
UPLOAD_BASE = Path("uploads")


class DocumentService:
    """Service for document file operations"""

    @staticmethod
    def validate_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate file type and size

        Returns:
            (is_valid, error_message)
        """
        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"

        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

        return True, None

    @staticmethod
    def generate_file_path(original_filename: str, folder: str = "/") -> tuple[str, str, str]:
        """
        Generate unique file path for storage

        Returns:
            (file_path, stored_filename, mime_type)
        """
        # Get file extension
        ext = os.path.splitext(original_filename)[1].lower()

        # Generate unique filename
        unique_id = str(uuid.uuid4())
        safe_name = secure_filename(os.path.splitext(original_filename)[0])
        stored_filename = f"{unique_id}_{safe_name}{ext}"

        # Create year/month directory structure
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')

        # Build full path
        file_path = os.path.join(str(STORAGE_BASE), year, month, stored_filename)

        # Get MIME type
        mime_type = MIME_TYPE_MAP.get(ext, 'application/octet-stream')

        return file_path, stored_filename, mime_type

    @staticmethod
    def ensure_directory(file_path: str) -> None:
        """Ensure directory exists for file path"""
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def save_upload_file(file_content: bytes, file_path: str) -> None:
        """
        Save uploaded file to disk

        Args:
            file_content: File content as bytes
            file_path: Destination path
        """
        DocumentService.ensure_directory(file_path)

        with open(file_path, 'wb') as f:
            f.write(file_content)

    @staticmethod
    def _save_file(file_content: bytes, filename: str, original_filename: str) -> str:
        """
        Save file with generated path (used for document generation).

        Args:
            file_content: File content as bytes
            filename: Filename to use
            original_filename: Original filename for extension detection

        Returns:
            Generated file path
        """
        file_path, _, _ = DocumentService.generate_file_path(original_filename)
        # Use the provided filename instead of generated one
        file_path = os.path.join(
            os.path.dirname(file_path),
            filename
        )
        DocumentService.save_upload_file(file_content, file_path)
        return file_path

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete file from disk

        Returns:
            True if deleted, False if not found
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False

    @staticmethod
    def get_file_type(filename: str) -> str:
        """Get file type from filename"""
        ext = os.path.splitext(filename)[1].lower()

        type_map = {
            '.pdf': 'PDF',
            '.docx': 'Word',
            '.doc': 'Word',
            '.xlsx': 'Excel',
            '.xls': 'Excel',
        }

        return type_map.get(ext, 'Unknown')

    @staticmethod
    def create_document(
        db: Session,
        original_filename: str,
        file_size: int,
        file_content: bytes,
        owner_id: int,
        folder: str = "/"
    ) -> Document:
        """
        Create document record and save file

        Args:
            db: Database session
            original_filename: Original uploaded filename
            file_size: File size in bytes
            file_content: File content as bytes
            owner_id: ID of user uploading
            folder: Folder path

        Returns:
            Created Document instance
        """
        # Validate file
        is_valid, error = DocumentService.validate_file(original_filename, file_size)
        if not is_valid:
            raise ValueError(error)

        # Generate file path
        file_path, stored_filename, mime_type = DocumentService.generate_file_path(
            original_filename, folder
        )

        # Save file to disk
        DocumentService.save_upload_file(file_content, file_path)

        # Get file type
        file_type = DocumentService.get_file_type(original_filename)

        # Create database record
        document = Document(
            filename=stored_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            folder=folder,
            owner_id=owner_id
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def get_document(db: Session, document_id: int) -> Optional[Document]:
        """Get document by ID"""
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def list_documents(
        db: Session,
        owner_id: Optional[int] = None,
        folder: Optional[str] = None,
        file_type: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Document], int]:
        """
        List documents with filters and pagination

        Returns:
            (documents, total_count)
        """
        query = db.query(Document)

        # Apply filters
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)

        if folder:
            query = query.filter(Document.folder == folder)

        if file_type:
            query = query.filter(Document.file_type == file_type)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Document.original_filename.ilike(search_filter)) |
                (Document.summary.ilike(search_filter))
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        return documents, total

    @staticmethod
    def update_document(
        db: Session,
        document_id: int,
        update_data: DocumentUpdate
    ) -> Optional[Document]:
        """Update document metadata"""
        document = DocumentService.get_document(db, document_id)
        if not document:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(document, key, value)

        document.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        """
        Delete document and its file

        Returns:
            True if deleted, False if not found
        """
        document = DocumentService.get_document(db, document_id)
        if not document:
            return False

        # Delete file from disk
        DocumentService.delete_file(document.file_path)

        # Delete from database (cascades to chunks)
        db.delete(document)
        db.commit()

        return True

    @staticmethod
    def get_document_stats(db: Session, owner_id: Optional[int] = None) -> dict:
        """Get statistics about documents"""
        query = db.query(Document)

        if owner_id:
            query = query.filter(Document.owner_id == owner_id)

        total = query.count()
        total_size = query.with_entities(func.sum(Document.file_size)).scalar() or 0

        # Count by file type
        by_type = {}
        type_counts = db.query(
            Document.file_type,
            func.count(Document.id)
        ).group_by(Document.file_type)

        if owner_id:
            type_counts = type_counts.filter(Document.owner_id == owner_id)

        for file_type, count in type_counts.all():
            by_type[file_type] = count

        # Count by folder
        by_folder = {}
        folder_counts = db.query(
            Document.folder,
            func.count(Document.id)
        ).group_by(Document.folder)

        if owner_id:
            folder_counts = folder_counts.filter(Document.owner_id == owner_id)

        for folder, count in folder_counts.all():
            by_folder[folder] = count

        # Count processed vs unprocessed
        processed = query.filter(Document.extracted_text.isnot(None)).count()
        unprocessed = total - processed

        return {
            'total_documents': total,
            'total_size_bytes': total_size,
            'by_file_type': by_type,
            'by_folder': by_folder,
            'processed_count': processed,
            'unprocessed_count': unprocessed,
        }
